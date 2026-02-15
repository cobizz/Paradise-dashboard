import os
import sys
from datetime import datetime
from pathlib import Path

# Ajouter le chemin du projet pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session, render_template_string
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
import requests
from dotenv import load_dotenv

# Importer les modules locaux
try:
    from bot_api import get_bot_stats, get_moderation_actions, get_active_giveaways
except ImportError:
    # Fonctions factices si le module n'existe pas
    def get_bot_stats():
        return {'servers': 5, 'members': 100, 'commands': 50, 'active_giveaways': 2, 'uptime': 3600, 'cogs': 8}
    def get_moderation_actions(limit=5):
        return []
    def get_active_giveaways():
        return []

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///paradise.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de la base de données
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ==================== MODÈLES ====================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    avatar = db.Column(db.String(200))
    is_owner = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GuildConfig(db.Model):
    __tablename__ = 'guild_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(80), unique=True, nullable=False)
    guild_name = db.Column(db.String(100))
    guild_icon = db.Column(db.String(200))
    prefix = db.Column(db.String(10), default='!')
    language = db.Column(db.String(10), default='fr')
    log_channel_id = db.Column(db.String(80))
    mod_log_channel_id = db.Column(db.String(80))
    message_log_channel_id = db.Column(db.String(80))
    voice_log_channel_id = db.Column(db.String(80))
    member_log_channel_id = db.Column(db.String(80))
    welcome_enabled = db.Column(db.Boolean, default=True)
    welcome_channel_id = db.Column(db.String(80))
    welcome_message = db.Column(db.Text, default='Bienvenue {member} sur {server} !')
    welcome_dm_enabled = db.Column(db.Boolean, default=False)
    welcome_dm_message = db.Column(db.Text, default='Bienvenue sur {server} !')
    leave_enabled = db.Column(db.Boolean, default=True)
    leave_channel_id = db.Column(db.String(80))
    leave_message = db.Column(db.Text, default='{member} nous a quittés...')
    auto_role_id = db.Column(db.String(80))
    muted_role_id = db.Column(db.String(80))
    auto_mod_enabled = db.Column(db.Boolean, default=True)
    bad_words_enabled = db.Column(db.Boolean, default=True)
    bad_words_action = db.Column(db.String(20), default='delete')
    invites_enabled = db.Column(db.Boolean, default=True)
    invites_action = db.Column(db.String(20), default='delete')
    caps_enabled = db.Column(db.Boolean, default=True)
    caps_percentage = db.Column(db.Integer, default=70)
    caps_min_length = db.Column(db.Integer, default=10)
    giveaway_channel_id = db.Column(db.String(80))
    custom_commands = db.Column(db.Text, default='{}')
    total_warns = db.Column(db.Integer, default=0)
    total_kicks = db.Column(db.Integer, default=0)
    total_bans = db.Column(db.Integer, default=0)
    total_mutes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'guild_id': self.guild_id,
            'guild_name': self.guild_name,
            'guild_icon': self.guild_icon,
            'prefix': self.prefix,
            'language': self.language,
            'log_channel_id': self.log_channel_id,
            'mod_log_channel_id': self.mod_log_channel_id,
            'message_log_channel_id': self.message_log_channel_id,
            'voice_log_channel_id': self.voice_log_channel_id,
            'member_log_channel_id': self.member_log_channel_id,
            'welcome_enabled': self.welcome_enabled,
            'welcome_channel_id': self.welcome_channel_id,
            'welcome_message': self.welcome_message,
            'welcome_dm_enabled': self.welcome_dm_enabled,
            'welcome_dm_message': self.welcome_dm_message,
            'leave_enabled': self.leave_enabled,
            'leave_channel_id': self.leave_channel_id,
            'leave_message': self.leave_message,
            'auto_role_id': self.auto_role_id,
            'muted_role_id': self.muted_role_id,
            'auto_mod_enabled': self.auto_mod_enabled,
            'bad_words_enabled': self.bad_words_enabled,
            'bad_words_action': self.bad_words_action,
            'invites_enabled': self.invites_enabled,
            'invites_action': self.invites_action,
            'caps_enabled': self.caps_enabled,
            'caps_percentage': self.caps_percentage,
            'caps_min_length': self.caps_min_length,
            'giveaway_channel_id': self.giveaway_channel_id,
            'custom_commands': json.loads(self.custom_commands) if self.custom_commands else {},
            'total_warns': self.total_warns,
            'total_kicks': self.total_kicks,
            'total_bans': self.total_bans,
            'total_mutes': self.total_mutes
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Créer les tables
with app.app_context():
    db.create_all()
    print("✅ Base de données initialisée")

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Page d'accueil publique"""
    return render_template('index.html')

@app.route('/debug')
def debug():
    """Page de débogage pour voir les templates disponibles"""
    templates = app.jinja_env.list_templates()
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug - Templates</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #1a1a1a; color: white; }
            h1 { color: #5865F2; }
            ul { list-style: none; padding: 0; }
            li { padding: 8px; margin: 5px 0; background: #2a2a2a; border-radius: 5px; }
            .ok { color: #57F287; }
            .missing { color: #ED4245; }
        </style>
    </head>
    <body>
        <h1>🔍 Debug - Templates disponibles</h1>
        <ul>
        {% for template in templates %}
            <li class="ok">✅ {{ template }}</li>
        {% endfor %}
        </ul>
        <p>Total: {{ templates|length }} templates</p>
    </body>
    </html>
    """, templates=templates)

@app.route('/invite')
def invite_page():
    """Page d'invitation du bot"""
    return render_template('invite.html', 
                         client_id=os.getenv('DISCORD_CLIENT_ID', ''),
                         permissions='8')

@app.route('/commands')
def commands_page():
    """Page des commandes"""
    return render_template('commands.html')

@app.route('/login')
def discord_login():
    """Redirection vers Discord OAuth2"""
    discord_oauth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={os.getenv('DISCORD_CLIENT_ID')}"
        f"&redirect_uri={os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:5000/callback')}"
        f"&response_type=code"
        f"&scope=identify%20guilds"
    )
    return redirect(discord_oauth_url)

@app.route('/callback')
def discord_callback():
    """Callback après authentification Discord"""
    code = request.args.get('code')
    
    if not code:
        flash("Code d'authentification manquant", 'danger')
        return redirect(url_for('index'))
    
    # Échanger le code contre un token
    data = {
        'client_id': os.getenv('DISCORD_CLIENT_ID'),
        'client_secret': os.getenv('DISCORD_CLIENT_SECRET'),
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:5000/callback'),
        'scope': 'identify guilds'
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers, timeout=10)
        credentials = response.json()
        
        if 'access_token' not in credentials:
            flash("Erreur d'authentification Discord", 'danger')
            return redirect(url_for('index'))
        
        access_token = credentials['access_token']
        
        # Récupérer les informations utilisateur
        user_response = requests.get('https://discord.com/api/users/@me', headers={
            'Authorization': f'Bearer {access_token}'
        }, timeout=10)
        user_data = user_response.json()
        
        # Construire l'URL de l'avatar
        if user_data.get('avatar'):
            avatar_url = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png"
        else:
            avatar_url = f"https://cdn.discordapp.com/embed/avatars/{int(user_data.get('discriminator', 0)) % 5}.png"
        
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
        }, timeout=10)
        guilds = guilds_response.json()
        
        # Filtrer les serveurs où l'utilisateur a les permissions admin
        user_guilds = [g for g in guilds if (g.get('permissions', 0) & 0x8)]
        session['guilds'] = user_guilds
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f"Erreur de connexion: {str(e)}", 'danger')
        return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal de l'utilisateur"""
    guilds = session.get('guilds', [])
    
    # Statistiques
    stats = {
        'servers': len(guilds),
        'members': sum(g.get('approximate_member_count', 0) for g in guilds),
        'managed_servers': len(guilds),
        'active_giveaways': 0
    }
    
    return render_template('dashboard.html', 
                         stats=stats,
                         guilds=guilds[:6],
                         user=current_user)

@app.route('/dashboard/guild/<guild_id>')
@login_required
def guild_dashboard(guild_id):
    """Dashboard de configuration pour un serveur spécifique"""
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
            guild_name=guild.get('name', 'Inconnu'),
            guild_icon=f"https://cdn.discordapp.com/icons/{guild_id}/{guild.get('icon')}.png" if guild.get('icon') else None
        )
        db.session.add(config)
        db.session.commit()
    
    return render_template('guild_dashboard.html', 
                         guild=guild,
                         config=config.to_dict())

@app.route('/moderation')
@login_required
def moderation():
    if not current_user.is_owner:
        flash("Accès réservé au propriétaire", 'danger')
        return redirect(url_for('dashboard'))
    return render_template('moderation.html')

@app.route('/giveaways')
@login_required
def giveaways():
    if not current_user.is_owner:
        flash("Accès réservé au propriétaire", 'danger')
        return redirect(url_for('dashboard'))
    return render_template('giveaways.html')

@app.route('/logs')
@login_required
def logs():
    if not current_user.is_owner:
        flash("Accès réservé au propriétaire", 'danger')
        return redirect(url_for('dashboard'))
    return render_template('logs.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index'))

# ==================== API ROUTES ====================

@app.route('/api/bot/stats')
@login_required
def api_bot_stats():
    if not current_user.is_owner:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify(get_bot_stats())

@app.route('/api/user/guilds')
@login_required
def api_user_guilds():
    return jsonify(session.get('guilds', []))

# ==================== LANCEMENT ====================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
