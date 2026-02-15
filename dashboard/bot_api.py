import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration de l'API du bot
BOT_API_URL = os.getenv('BOT_API_URL', 'http://localhost:5001')
BOT_API_KEY = os.getenv('BOT_API_KEY', 'your-secret-key')

def get_bot_stats():
    """Récupère les statistiques du bot"""
    try:
        response = requests.get(
            f"{BOT_API_URL}/api/stats",
            headers={'X-API-Key': BOT_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Erreur API stats: {e}")
    
    # Données par défaut si l'API n'est pas disponible
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
    except Exception as e:
        print(f"Erreur API moderation: {e}")
    
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
    except Exception as e:
        print(f"Erreur API giveaways: {e}")
    
    return []

def end_giveaway(message_id):
    """Termine un giveaway"""
    try:
        response = requests.post(
            f"{BOT_API_URL}/api/giveaway/{message_id}/end",
            headers={'X-API-Key': BOT_API_KEY},
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Erreur API end giveaway: {e}")
    
    return False

def get_servers():
    """Récupère la liste des serveurs"""
    try:
        response = requests.get(
            f"{BOT_API_URL}/api/servers",
            headers={'X-API-Key': BOT_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Erreur API servers: {e}")
    
    return []

def get_logs(limit=100):
    """Récupère les logs"""
    try:
        response = requests.get(
            f"{BOT_API_URL}/api/logs",
            params={'limit': limit},
            headers={'X-API-Key': BOT_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Erreur API logs: {e}")
    
    return []
