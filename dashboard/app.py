import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Ajouter le chemin parent pour importer les modules du bot
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, render_template, redirect, url_for, session, request, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import aiohttp
import asyncio
from dotenv import load_dotenv

# Importer les modules du bot
from bot import ParadiseBot
from config.settings import Settings
from utils.database import Database

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dashboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Importer les modèles après l'initialisation de db
from models import User, Server, ModerationAction, Giveaway

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== ROUTES D'AUTHENTIFICATION ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login')
def discord_login():
    # Redirection vers Discord OAuth2
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
        flash("Erreur d'authentification Discord", 'danger')  # LIGNE CORRIGÉE (guillemets doubles)
        return redirect(url_for('index'))
    
    access_token = credentials['access_token']
    
    # Récupérer les informations utilisateur
    user_response = requests.get('https://discord.com/api/users/@me', headers={
        'Authorization': f'Bearer {access_token}'
    })
    user_data = user_response.json()
    
    # Récupérer l'avatar
    avatar_url = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png"
    
    # Vérifier si l'utilisateur est le propriétaire
    is_owner = (int(user_data['id']) == 1274391702655864883)  # Votre ID
    
    # Créer ou mettre à jour l'utilisateur
    user = User.query.filter_by(discord_id=user_data['id']).first()
    if not user:
        user = User(
            discord_id=user_data['id'],
            username=user_data['username'],
            avatar=avatar_url,
            is_owner=is_owner,
            is_admin=is_owner
        )
        db.session.add(user)
    else:
        user.username = user_data['username']
        user.avatar = avatar_url
        user.last_login = datetime.utcnow()
    
    db.session.commit()
    
    login_user(user)
    
    # Récupérer la liste des serveurs
    guilds_response = requests.get('https://discord.com/api/users/@me/guilds', headers={
        'Authorization': f'Bearer {access_token}'
    })
    guilds = guilds_response.json()
    
    # Sauvegarder les serveurs en session
    session['guilds'] = guilds
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ==================== ROUTES PRINCIPALES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    # Créer une instance du bot pour accéder aux données
    bot = ParadiseBot()
    
    # Récupérer les statistiques
    total_servers = len(bot.guilds) if hasattr(bot, 'guilds') else 0
    total_members = sum(g.member_count for g in bot.guilds) if hasattr(bot, 'guilds') else 0
    total_commands = len(bot.commands) if hasattr(bot, 'commands') else 0
    
    giveaways_cog = bot.get_cog('Giveaways')
    active_giveaways = 0
    if giveaways_cog and hasattr(giveaways_cog, 'active_giveaways'):
        active_giveaways = len([g for g in giveaways_cog.active_giveaways.values() if not g['ended']])
    
    # Préparer les données du graphique
    last_7_days = [(datetime.now() - timedelta(days=i)).strftime('%d/%m') for i in range(6, -1, -1)]
    actions_data = [0, 0, 0, 0, 0, 0, 0]  # Valeurs par défaut
    
    # Dernières actions
    recent_actions = []
    
    # Giveaways actifs
    active_gw = []
    if giveaways_cog and hasattr(giveaways_cog, 'active_giveaways'):
        active_gw = [g for g in giveaways_cog.active_giveaways.values() if not g['ended']]
    
    return render_template('dashboard.html',
                         stats={
                             'servers': total_servers,
                             'members': total_members,
                             'commands': total_commands,
                             'active_giveaways': active_giveaways
                         },
                         chart_labels=json.dumps(last_7_days),
                         chart_data=json.dumps(actions_data),
                         recent_actions=recent_actions,
                         active_giveaways=active_gw[:5])

@app.route('/servers')
@login_required
def servers():
    bot = ParadiseBot()
    servers = []
    
    for guild in bot.guilds:
        bot_in_guild = guild.get_member(bot.user.id) is not None
        servers.append({
            'id': guild.id,
            'name': guild.name,
            'icon': guild.icon.url if guild.icon else None,
            'member_count': guild.member_count,
            'bot_in': bot_in_guild,
            'owner': guild.owner.name if guild.owner else 'Inconnu'
        })
    
    return render_template('servers.html', servers=servers)

@app.route('/moderation')
@login_required
def moderation():
    if not current_user.is_owner:
        flash('Accès réservé au propriétaire', 'danger')
        return redirect(url_for('dashboard'))
    
    # Récupérer l'historique de modération
    actions = []  # À implémenter avec votre base de données
    
    return render_template('moderation.html', actions=actions)

@app.route('/giveaways')
@login_required
def giveaways():
    bot = ParadiseBot()
    giveaways_cog = bot.get_cog('Giveaways')
    all_giveaways = []
    
    if giveaways_cog and hasattr(giveaways_cog, 'active_giveaways'):
        all_giveaways = giveaways_cog.active_giveaways.values()
    
    active = [g for g in all_giveaways if not g['ended']]
    ended = [g for g in all_giveaways if g['ended']]
    
    return render_template('giveaways.html', active=active, ended=ended)

@app.route('/logs')
@login_required
def logs():
    if not current_user.is_owner:
        flash('Accès réservé au propriétaire', 'danger')
        return redirect(url_for('dashboard'))
    
    # Récupérer les logs depuis la base de données
    logs = []  # À implémenter
    
    return render_template('logs.html', logs=logs)

# ==================== API ROUTES ====================

@app.route('/api/giveaway/<message_id>/end', methods=['POST'])
@login_required
def api_end_giveaway(message_id):
    if not current_user.is_owner:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({'error': 'Not implemented'}), 501

@app.route('/api/bot/stats')
@login_required
def api_bot_stats():
    bot = ParadiseBot()
    uptime = datetime.now() - bot.start_time if hasattr(bot, 'start_time') else timedelta(0)
    
    return jsonify({
        'servers': len(bot.guilds) if hasattr(bot, 'guilds') else 0,
        'members': sum(g.member_count for g in bot.guilds) if hasattr(bot, 'guilds') else 0,
        'commands': len(bot.commands) if hasattr(bot, 'commands') else 0,
        'uptime': uptime.total_seconds(),
        'cogs': len(bot.cogs) if hasattr(bot, 'cogs') else 0
    })

# ==================== LANCEMENT ====================

if __name__ == '__main__':
    # Créer les tables
    with app.app_context():
        db.create_all()
    
    # Lancer le dashboard
    app.run(host='0.0.0.0', port=5000, debug=True)