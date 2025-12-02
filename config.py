import spotipy
import requests
import json
import os
import base64
from spotipy.oauth2 import SpotifyOAuth
from difflib import SequenceMatcher
import time
from dotenv import load_dotenv
import telethon
import asyncio
from urllib.parse import urlparse

# telegram
## app api
TELEGRAM_APP_API_ID = os.environ.get('DEVELOPER_TELEGRAM_APP_API_ID')
TELEGRAM_APP_API_HASH= os.environ.get('DEVELOPER_TELEGRAM_APP_API_HASH')
TELEGRAM_PHONE_NUMBER= os.environ.get('DEVELOPER_TELEGRAM_PHONE_NUMBER')
session_name = "developer_account"

# Load environment variables from .env file
load_dotenv()

# warp
## proxy
warp_proxies = os.environ["WARP_PROXIES"]
warp_proxies = json.loads(warp_proxies)
## session
warp_session = requests.Session()
warp_session.proxies.update(warp_proxies)
# tuple - to be used by telethon
warp_proxies_tuple = urlparse(warp_proxies['http'])
warp_proxies_tuple = (
    warp_proxies_tuple.scheme.replace('h', ''),  # 'socks5h' → 'socks5'
    warp_proxies_tuple.hostname,
    warp_proxies_tuple.port,
    bool(warp_proxies_tuple.username and warp_proxies_tuple.password),
    warp_proxies_tuple.username,
    warp_proxies_tuple.password
)

# Configuration de l'authentification
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
        scope='playlist-modify-public playlist-modify-private ugc-image-upload',
        cache_path='.cache',
        show_dialog=False
    ),
    requests_session=warp_session,
)

# Obtenir l'ID de l'utilisateur connecté
user_id = sp.current_user()["id"]

# Seuil de similarité minimum (ajustez selon vos besoins)
SIMILARITY_THRESHOLD = 0.6

# max telegram channel messages count
MAX_MESSAGES_COUNT = 20000