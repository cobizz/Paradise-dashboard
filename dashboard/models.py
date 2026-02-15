from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    avatar = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    is_owner = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(200))
    member_count = db.Column(db.Integer, default=0)
    bot_in_server = db.Column(db.Boolean, default=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class ModerationAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(80), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # warn, kick, ban, mute
    user_id = db.Column(db.String(80), nullable=False)
    user_name = db.Column(db.String(100))
    moderator_id = db.Column(db.String(80), nullable=False)
    moderator_name = db.Column(db.String(100))
    reason = db.Column(db.Text)
    duration = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Giveaway(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(80), unique=True)
    server_id = db.Column(db.String(80), nullable=False)
    channel_id = db.Column(db.String(80), nullable=False)
    prize = db.Column(db.String(200), nullable=False)
    winners = db.Column(db.Integer, default=1)
    entrants = db.Column(db.Integer, default=0)
    host_id = db.Column(db.String(80), nullable=False)
    host_name = db.Column(db.String(100))
    end_time = db.Column(db.DateTime)
    ended = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)