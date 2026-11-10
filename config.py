import requests
import json
import os
import base64
from difflib import SequenceMatcher
from dotenv import load_dotenv
import httpx

# Load environment variables from .env file
load_dotenv()

## private-router (Telethon + Spotify)
# Search/metadata → diamond Premium developer app on the router.
# Playlist create/cover/replace → playlistify Spotify user OAuth on the router.
PRIVATE_ROUTER_URL = os.environ.get('PRIVATE_ROUTER_URL', 'http://127.0.0.1:3010').rstrip('/')
PRIVATE_ROUTER_TOKEN = os.environ.get('PRIVATE_ROUTER_TOKEN', '')

# warp (kept for any direct HTTP that still needs it)
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


def _router_headers():
    if not PRIVATE_ROUTER_TOKEN:
        raise RuntimeError('PRIVATE_ROUTER_TOKEN is not set')
    return {'Authorization': f'Bearer {PRIVATE_ROUTER_TOKEN}'}


def private_router_post(path, payload, timeout=120.0):
    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            f'{PRIVATE_ROUTER_URL}{path}',
            headers=_router_headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json()


def private_router_get(path, timeout=60.0):
    with httpx.Client(timeout=timeout) as client:
        response = client.get(
            f'{PRIVATE_ROUTER_URL}{path}',
            headers=_router_headers(),
        )
        response.raise_for_status()
        return response.json()


def private_router_channel_music(username, limit=MAX_MESSAGES_COUNT, include_profile_photo=True):
    return private_router_post(
        '/v1/channels/music',
        {
            'username': username.lstrip('@'),
            'limit': limit,
            'include_profile_photo': include_profile_photo,
        },
        timeout=600.0,
    )


def private_router_spotify_search(query, limit=1):
    return private_router_post(
        '/v1/spotify/search',
        {'q': query, 'type': 'track', 'limit': limit},
    )


def private_router_spotify_create_playlist(name, description='', public=True):
    return private_router_post(
        '/v1/spotify/playlists/create',
        {'name': name, 'description': description, 'public': public},
    )


def private_router_spotify_cover(playlist_id, image_base64):
    return private_router_post(
        '/v1/spotify/playlists/cover',
        {'playlist_id': playlist_id, 'image_base64': image_base64},
    )


def private_router_spotify_replace(playlist_id, uris):
    return private_router_post(
        '/v1/spotify/playlists/replace',
        {'playlist_id': playlist_id, 'uris': uris},
        timeout=600.0,
    )
