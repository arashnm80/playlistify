from config import *  # noqa: F403


def fetch_channel_musics_and_profile(messages_count, channel_username):
    """Fetch music catalog + profile photo via private-router (no local Telethon)."""
    print("Requesting channel music from private-router...")
    data = private_router_channel_music(channel_username, limit=messages_count)

    musics = data.get("musics") or {}
    with open("musics.json", "w", encoding="utf-8") as f:
        json.dump(musics, f, indent=2, ensure_ascii=False)

    photo_b64 = data.get("profile_photo_base64")
    if photo_b64:
        with open("image.jpg", "wb") as f:
            f.write(base64.b64decode(photo_b64))
        print("Saved profile photo to image.jpg")
    else:
        print("No profile photo returned")

    print(f"Fetched {data.get('fetched_messages', 0)} music messages.")
    print(f"Saved {len(musics)} valid music entries to musics.json.")
    for msg_id, song in musics.items():
        print("------------")
        print(f"Message ID: {msg_id}")
        print(f"Titre: {song.get('title')}")
        print(f"Artiste: {song.get('artist')}")


def create_new_playlist(telegram_channel_username):
    '''
    create new playlist for channel and set title, description and image for it
    '''
    playlist = private_router_spotify_create_playlist(
        name=f"t.me/{telegram_channel_username}",
        description="automatically generated playlist from tracks in telegram channel. developer: Arashnm80",
        public=True,
    )
    playlist_id = playlist["id"]

    with open("image.jpg", "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("ascii")
    private_router_spotify_cover(playlist_id, image_data)

    print("Playlist ID:", playlist_id)
    return playlist_id

def set_playlist_tracks(playlist_id):
    '''
    set tracks for given playlist id based on musics.json file
    matches songs based on similarity threshold
    '''
    with open('musics.json', 'r') as f:
        musics_json = json.load(f)

    song_names = [f"{song_data['title']} - {song_data['artist']}" for song_id, song_data in musics_json.items()]

    def calculate_similarity(a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    track_uris = []
    total_songs = len(song_names)
    for i, song in enumerate(song_names):
        prefix = f"{i+1} / {total_songs}: "
        result = private_router_spotify_search(song, limit=1)
        tracks = result.get("items") or []
        if tracks:
            found_track = tracks[0]
            found_track_name = found_track.get("name") or ""
            artists = found_track.get("artists") or []
            found_track_artists = ", ".join(
                [(a.get("name") if isinstance(a, dict) else str(a)) for a in artists]
            )
            found_track_full = f"{found_track_name} - {found_track_artists}"
            similarity_score = calculate_similarity(song, found_track_full)
            if similarity_score >= SIMILARITY_THRESHOLD:
                track_uris.append(found_track.get("uri") or f"spotify:track:{found_track['id']}")
                print(f"{prefix}✅ Trouvé: {song} (Similarité: {similarity_score:.2%})")
            else:
                print(f"{prefix}⚠️ Faible correspondance: {song} → {found_track_full} (Similarité: {similarity_score:.2%})")
        else:
            print(f"{prefix}❌ Introuvable: {song}")

    print("🗑️ Remplacement des pistes via private-router...")
    data = private_router_spotify_replace(playlist_id, track_uris)
    print(f"✅ Total: {data.get('added', 0)} titres ajoutés à la playlist.")
