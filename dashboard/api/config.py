from flask import Blueprint, request, jsonify
from ..models import db, GuildConfig
from functools import wraps
import os

config_api = Blueprint('config_api', __name__)

API_KEY = os.getenv('DASHBOARD_API_KEY', 'your-secret-key')

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated

@config_api.route('/guild/<guild_id>/config', methods=['GET'])
@require_api_key
def get_guild_config(guild_id):
    """Endpoint pour que le bot récupère la config d'un serveur"""
    config = GuildConfig.query.filter_by(guild_id=guild_id).first()
    if config:
        return jsonify(config.to_dict())
    return jsonify({'error': 'Not found'}), 404

@config_api.route('/guild/<guild_id>/config', methods=['POST'])
@require_api_key
def update_guild_config(guild_id):
    """Le bot peut mettre à jour la config depuis ses actions"""
    data = request.json
    config = GuildConfig.query.filter_by(guild_id=guild_id).first()
    if not config:
        config = GuildConfig(guild_id=guild_id)
        db.session.add(config)
    
    # Mettre à jour les champs
    for key, value in data.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    db.session.commit()
    return jsonify({'success': True})