from config import *

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
    sp, user_id = get_spotify()
    # Création de la playlist
    playlist = sp.user_playlist_create(
        user=user_id,
        name=f"t.me/{telegram_channel_username}",
        description="automatically generated playlist from tracks in telegram channel. developer: Arashnm80",
        public=True,  # ou False pour une playlist privée
    )

    # get id of generated playlist
    playlist_id = playlist["id"]

    # set image for playlsit
    with open("image.jpg", "rb") as image_file:
        image_data = base64.b64encode(image_file.read())

    sp.playlist_upload_cover_image(playlist_id, image_data)

    # Affichage de l'ID de la playlist créée
    print("Playlist ID:", playlist_id)

    # output to be used by the rest of the code
    return playlist_id

def set_playlist_tracks(playlist_id):
    '''
    set tracks for given playlist id based on musics.json file
    matches songs based on similarity threshold
    '''
    sp, _user_id = get_spotify()
    # Charger les données JSON depuis le fichier
    with open('musics.json', 'r') as f:
        musics_json = json.load(f)

    # Créer la liste des chansons au format "titre - artiste"
    song_names = [f"{song_data['title']} - {song_data['artist']}" for song_id, song_data in musics_json.items()]

    # Effacer toutes les pistes existantes de la playlist
    print("🗑️ Suppression de toutes les pistes existantes de la playlist...")
    playlist_tracks = sp.playlist_items(playlist_id)
    if playlist_tracks['items']:
        track_ids = [item['track']['id'] for item in playlist_tracks['items']]
        sp.playlist_remove_all_occurrences_of_items(playlist_id, track_ids)
        print(f"✅ {len(track_ids)} pistes supprimées de la playlist.")
    else:
        print("ℹ️ La playlist est déjà vide.")

    # Rechercher chaque chanson et ajouter à la playlist
    track_uris = []

    # Fonction pour calculer la similarité entre deux chaînes de caractères
    def calculate_similarity(a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    total_songs = len(song_names)
    for i, song in enumerate(song_names):
        prefix = f"{i+1} / {total_songs}: "
        result = sp.search(q=song, limit=1, type="track")
        tracks = result.get("tracks", {}).get("items", [])
        if tracks:
            # Extraire les informations du morceau trouvé
            found_track = tracks[0]
            found_track_name = found_track["name"]
            found_track_artists = ", ".join([artist["name"] for artist in found_track["artists"]])
            found_track_full = f"{found_track_name} - {found_track_artists}"
            
            # Calculer le score de similarité
            similarity_score = calculate_similarity(song, found_track_full)
            
            if similarity_score >= SIMILARITY_THRESHOLD:
                track_uris.append(found_track["uri"])
                print(f"{prefix}✅ Trouvé: {song} (Similarité: {similarity_score:.2%})")
            else:
                print(f"{prefix}⚠️ Faible correspondance: {song} → {found_track_full} (Similarité: {similarity_score:.2%})")
        else:
            print(f"{prefix}❌ Introuvable: {song}")

    # Ajouter les morceaux trouvés à la playlist par lots de 100 maximum
    if track_uris:
        # Diviser les pistes en lots de 100 maximum
        batch_size = 100
        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i:i+batch_size]
            sp.playlist_add_items(playlist_id, batch)
            print(f"✅ Lot {i//batch_size + 1}: {len(batch)} titres ajoutés à la playlist.")
            # Add 1 second pause between batches
            time.sleep(1)
        
        print(f"✅ Total: {len(track_uris)} titres ajoutés à la playlist.")
    else:
        print("⚠️ Aucun morceau trouvé à ajouter.")