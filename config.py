import spotipy
import requests
import json
import os
import base64
from spotipy.oauth2 import SpotifyOAuth
from difflib import SequenceMatcher
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# warp socks proxy
warp_proxies = os.environ["WARP_PROXIES"]
warp_proxies = json.loads(warp_proxies)
warp_session = requests.Session()
warp_session.proxies.update(warp_proxies)

# Configuration de l'authentification
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
    scope='playlist-modify-public playlist-modify-private ugc-image-upload',
    cache_path='.cache',
    show_dialog=False
), requests_session=warp_session)

# Obtenir l'ID de l'utilisateur connecté
user_id = sp.current_user()["id"]

# Seuil de similarité minimum (ajustez selon vos besoins)
SIMILARITY_THRESHOLD = 0.6