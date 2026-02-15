import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration de l'API (à créer sur ton bot)
BOT_API_URL = os.getenv('BOT_API_URL', 'http://localhost:5001')  # URL de ton bot sur Pella
BOT_API_KEY = os.getenv('BOT_API_KEY', 'your-secret-key')  # Clé secrète pour sécuriser

def get_bot_stats():
    """Récupère les stats du bot via API"""
    try:
        response = requests.get(
            f"{BOT_API_URL}/api/stats",
            headers={'X-API-Key': BOT_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {
        'servers': 0,
        'members': 0,
        'commands': 0,
        'active_giveaways': 0,
        'uptime': 0,
        'cogs': 0
    }

def get_moderation_actions(limit=10):
    """Récupère les dernières actions de modération"""
    try:
        response = requests.get(
            f"{BOT_API_URL}/api/moderation/latest",
            params={'limit': limit},
            headers={'X-API-Key': BOT_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def get_active_giveaways():
    """Récupère les giveaways actifs"""
    try:
        response = requests.get(
            f"{BOT_API_URL}/api/giveaways/active",
            headers={'X-API-Key': BOT_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []
