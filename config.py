import spotipy
import requests
import json
import os
import base64
import sys
from spotipy.oauth2 import SpotifyOAuth
from difflib import SequenceMatcher
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if WARP proxy should be used (command line argument)
use_warp = '--warp' in sys.argv or '--proxy' in sys.argv

# Setup session with or without WARP proxy
if use_warp:
    try:
        warp_proxies = os.environ.get("WARP_PROXIES")
        if warp_proxies:
            warp_proxies = json.loads(warp_proxies)
            session = requests.Session()
            session.proxies.update(warp_proxies)
            print("Using WARP proxy for requests")
        else:
            print("WARP proxy requested but WARP_PROXIES not found in .env file")
            session = requests.Session()
    except Exception as e:
        print(f"Error setting up WARP proxy: {e}")
        print("Falling back to direct connection")
        session = requests.Session()
else:
    session = requests.Session()

# Configuration de l'authentification
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:8080'),
    scope='playlist-modify-public playlist-modify-private ugc-image-upload',
    cache_path='.cache',
    show_dialog=False
), requests_session=session)

# Obtenir l'ID de l'utilisateur connecté
user_id = sp.current_user()["id"]

# Seuil de similarité minimum (ajustez selon vos besoins)
SIMILARITY_THRESHOLD = 0.6