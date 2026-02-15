import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.urandom(24).hex()
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dashboard.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ID du propriétaire du bot (vous)
    OWNER_ID = 1274391702655864883
    
    # Configuration du bot
    BOT_TOKEN = os.getenv('DISCORD_TOKEN')
    BOT_PREFIX = os.getenv('PREFIX', '!')