import os
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dashboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modèles de base de données
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    avatar = db.Column(db.String(200))
    is_owner = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login')
def discord_login():
    discord_oauth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={os.getenv('DISCORD_CLIENT_ID')}"
        f"&redirect_uri={os.getenv('DISCORD_REDIRECT_URI')}"
        f"&response_type=code"
        f"&scope=identify"
    )
    return redirect(discord_oauth_url)

@app.route('/callback')
def discord_callback():
    code = request.args.get('code')
    
    data = {
        'client_id': os.getenv('DISCORD_CLIENT_ID'),
        'client_secret': os.getenv('DISCORD_CLIENT_SECRET'),
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': os.getenv('DISCORD_REDIRECT_URI'),
        'scope': 'identify'
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
    
    avatar_url = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png"
    
    # Vérifier si c'est le propriétaire (votre ID)
    is_owner = (int(user_data['id']) == 1274391702655864883)
    
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
    
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Statistiques statiques pour l'instant
    stats = {
        'servers': 5,
        'members': 100,
        'commands': 50,
        'active_giveaways': 2
    }
    
    return render_template('dashboard.html', stats=stats)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/bot/stats')
@login_required
def api_bot_stats():
    if not current_user.is_owner:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'servers': 5,
        'members': 100,
        'commands': 50,
        'uptime': 3600,
        'cogs': 8
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
