import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Ajouter le chemin parent pour trouver les modules
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
import requests
from dotenv import load_dotenv

# Importer les modèles depuis le dossier courant
from .models import db, User, GuildConfig, ModerationLog, Giveaway
from .api.config import config_api

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///paradise.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialiser la base de données
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Enregistrer les blueprints
app.register_blueprint(config_api, url_prefix='/api')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Créer les tables
with app.app_context():
    db.create_all()
    print("✅ Base de données initialisée")

# ==================== ROUTES PUBLIQUES ====================

@app.route('/')
def index():
    """Page d'accueil publique"""
    return render_template('index.html')

@app.route('/invite')
def invite_page():
    """Page d'invitation du bot"""
    return render_template('invite.html', 
                         client_id=os.getenv('DISCORD_CLIENT_ID'),
                         permissions='8')

@app.route('/commands')
def commands_page():
    """Page des commandes"""
    return render_template('commands.html')

# ==================== ROUTES D'AUTHENTIFICATION ====================

@app.route('/login')
def discord_login():
    """Redirection vers Discord OAuth2"""
    discord_oauth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={os.getenv('DISCORD_CLIENT_ID')}"
        f"&redirect_uri={os.getenv('DISCORD_REDIRECT_URI')}"
        f"&response_type=code"
        f"&scope=identify%20guilds"
    )
    return redirect(discord_oauth_url)

@app.route('/callback')
def discord_callback():
    """Callback après authentification Discord"""
    code = request.args.get('code')
    
    # Échanger le code contre un token
    data = {
        'client_id': os.getenv('DISCORD_CLIENT_ID'),
        'client_secret': os.getenv('DISCORD_CLIENT_SECRET'),
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': os.getenv('DISCORD_REDIRECT_URI'),
        'scope': 'identify guilds'
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
    credentials = response.json()
    
    if 'access_token' not in credentials:
        flash("Erreur d'authentification Discord", 'danger')
        return redirect(url_for('index'))
    
    access_token = credentials['access_token']
    
    # Récupérer les informations utilisateur
    user_response = requests.get('https://discord.com/api/users/@me', headers={
        'Authorization': f'Bearer {access_token}'
    })
    user_data = user_response.json()
    
    avatar_url = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png" if user_data['avatar'] else f"https://cdn.discordapp.com/embed/avatars/{int(user_data['discriminator']) % 5}.png"
    
    # Vérifier si c'est le propriétaire
    is_owner = (int(user_data['id']) == 1274391702655864883)
    
    # Créer ou mettre à jour l'utilisateur
    user = User.query.filter_by(discord_id=user_data['id']).first()
    if not user:
        user = User(
            discord_id=user_data['id'],
            username=user_data['username'],
            avatar=avatar_url,
            is_owner=is_owner
        )
        db.session.add(user)
    else:
        user.username = user_data['username']
        user.avatar = avatar_url
        user.last_login = datetime.utcnow()
    
    db.session.commit()
    login_user(user)
    
    # Récupérer les serveurs de l'utilisateur
    guilds_response = requests.get('https://discord.com/api/users/@me/guilds', headers={
        'Authorization': f'Bearer {access_token}'
    })
    guilds = guilds_response.json()
    
    # Filtrer les serveurs où le bot est présent (à améliorer avec une vraie API)
    user_guilds = [g for g in guilds if (g['permissions'] & 0x8)]  # Admin
    
    session['guilds'] = user_guilds
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ==================== ROUTES PROTÉGÉES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal de l'utilisateur"""
    guilds = session.get('guilds', [])
    
    # Statistiques globales
    total_servers = len(guilds)
    total_members = 0  # À récupérer via API
    
    stats = {
        'servers': total_servers,
        'members': total_members,
        'managed_servers': len([g for g in guilds if g.get('bot_in')]),
        'active_giveaways': 0
    }
    
    return render_template('dashboard.html', 
                         stats=stats,
                         guilds=guilds[:6])

@app.route('/dashboard/guild/<guild_id>')
@login_required
def guild_dashboard(guild_id):
    """Dashboard de configuration pour un serveur spécifique"""
    # Vérifier que l'utilisateur a accès à ce serveur
    guilds = session.get('guilds', [])
    guild = next((g for g in guilds if g['id'] == guild_id), None)
    
    if not guild:
        flash("Vous n'avez pas accès à ce serveur", 'danger')
        return redirect(url_for('dashboard'))
    
    # Récupérer ou créer la configuration
    config = GuildConfig.query.filter_by(guild_id=guild_id).first()
    if not config:
        config = GuildConfig(
            guild_id=guild_id,
            guild_name=guild['name'],
            guild_icon=f"https://cdn.discordapp.com/icons/{guild_id}/{guild['icon']}.png" if guild['icon'] else None
        )
        db.session.add(config)
        db.session.commit()
    
    return render_template('guild_dashboard.html', 
                         guild=guild,
                         config=config.to_dict())

@app.route('/api/user/guilds')
@login_required
def get_user_guilds():
    """API pour récupérer les serveurs de l'utilisateur"""
    return jsonify(session.get('guilds', []))

# ==================== LANCEMENT ====================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
