import spotipy
import requests
import json
import os
import base64
from spotipy.oauth2 import SpotifyOAuth
from difflib import SequenceMatcher
import time
from dotenv import load_dotenv
import httpx

# Load environment variables from .env file
load_dotenv()

## private-router (owns the Telethon user session)
PRIVATE_ROUTER_URL = os.environ.get('PRIVATE_ROUTER_URL', 'http://127.0.0.1:3010').rstrip('/')
PRIVATE_ROUTER_TOKEN = os.environ.get('PRIVATE_ROUTER_TOKEN', '')

# warp
## proxy
warp_proxies = os.environ["WARP_PROXIES"]
warp_proxies = json.loads(warp_proxies)
## session
warp_session = requests.Session()
warp_session.proxies.update(warp_proxies)

# Seuil de similarité minimum (ajustez selon vos besoins)
SIMILARITY_THRESHOLD = 0.6

# max telegram channel messages count
MAX_MESSAGES_COUNT = 20000

_sp = None
_user_id = None


def get_spotify():
    """Lazy Spotify client so Telegram/router checks do not require a fresh Spotify token."""
    global _sp, _user_id
    if _sp is None:
        _sp = spotipy.Spotify(
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
        _user_id = _sp.current_user()["id"]
    return _sp, _user_id


def private_router_channel_music(username, limit=MAX_MESSAGES_COUNT, include_profile_photo=True):
    if not PRIVATE_ROUTER_TOKEN:
        raise RuntimeError('PRIVATE_ROUTER_TOKEN is not set')
    headers = {'Authorization': f'Bearer {PRIVATE_ROUTER_TOKEN}'}
    payload = {
        'username': username.lstrip('@'),
        'limit': limit,
        'include_profile_photo': include_profile_photo,
    }
    with httpx.Client(timeout=600.0) as client:
        response = client.post(
            f'{PRIVATE_ROUTER_URL}/v1/channels/music',
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()
