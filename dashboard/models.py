from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    avatar = db.Column(db.String(200))
    is_owner = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    guild_configs = db.relationship('GuildConfig', backref='owner', lazy=True)

class GuildConfig(db.Model):
    __tablename__ = 'guild_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(80), unique=True, nullable=False)
    guild_name = db.Column(db.String(100))
    guild_icon = db.Column(db.String(200))
    
    # Configuration générale
    prefix = db.Column(db.String(10), default='!')
    language = db.Column(db.String(10), default='fr')
    
    # Logs
    log_channel_id = db.Column(db.String(80))
    mod_log_channel_id = db.Column(db.String(80))
    message_log_channel_id = db.Column(db.String(80))
    voice_log_channel_id = db.Column(db.String(80))
    member_log_channel_id = db.Column(db.String(80))
    
    # Bienvenue
    welcome_enabled = db.Column(db.Boolean, default=True)
    welcome_channel_id = db.Column(db.String(80))
    welcome_message = db.Column(db.Text, default='Bienvenue {member} sur {server} !')
    welcome_dm_enabled = db.Column(db.Boolean, default=False)
    welcome_dm_message = db.Column(db.Text, default='Bienvenue sur {server} !')
    
    # Départs
    leave_enabled = db.Column(db.Boolean, default=True)
    leave_channel_id = db.Column(db.String(80))
    leave_message = db.Column(db.Text, default='{member} nous a quittés...')
    
    # Rôles
    auto_role_id = db.Column(db.String(80))
    muted_role_id = db.Column(db.String(80))
    
    # Auto-modération
    auto_mod_enabled = db.Column(db.Boolean, default=True)
    bad_words_enabled = db.Column(db.Boolean, default=True)
    bad_words_action = db.Column(db.String(20), default='delete')
    invites_enabled = db.Column(db.Boolean, default=True)
    invites_action = db.Column(db.String(20), default='delete')
    caps_enabled = db.Column(db.Boolean, default=True)
    caps_percentage = db.Column(db.Integer, default=70)
    caps_min_length = db.Column(db.Integer, default=10)
    
    # Giveaways
    giveaway_channel_id = db.Column(db.String(80))
    
    # Commandes personnalisées (stockées en JSON)
    custom_commands = db.Column(db.Text, default='{}')
    
    # Statistiques
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

class ModerationLog(db.Model):
    __tablename__ = 'moderation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(80), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.String(80), nullable=False)
    user_name = db.Column(db.String(100))
    moderator_id = db.Column(db.String(80), nullable=False)
    moderator_name = db.Column(db.String(100))
    reason = db.Column(db.Text)
    duration = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Giveaway(db.Model):
    __tablename__ = 'giveaways'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(80), unique=True)
    guild_id = db.Column(db.String(80), nullable=False)
    channel_id = db.Column(db.String(80), nullable=False)
    prize = db.Column(db.String(200), nullable=False)
    winners_count = db.Column(db.Integer, default=1)
    entrants = db.Column(db.Integer, default=0)
    host_id = db.Column(db.String(80), nullable=False)
    host_name = db.Column(db.String(100))
    end_time = db.Column(db.DateTime)
    ended = db.Column(db.Boolean, default=False)
    role_required = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
