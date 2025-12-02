from config import *

async def fetch_channel_musics_and_profile(telethon_client, messages_count, channel_username):
    async def safe_get_entity(username):
        try:
            print("Trying to get Telegram entity...")
            return await telethon_client.get_entity(username)
        except telethon.errors.FloodWaitError as e:
            print(f"Rate limited. Waiting {e.seconds} seconds.")
            await asyncio.sleep(e.seconds)
            return await safe_get_entity(username)
    
    async def fetch_messages_and_profile():
        channel = await safe_get_entity(channel_username)

        # get profile photo of channel
        await telethon_client.download_profile_photo(channel, file="image.jpg")

        messages = await telethon_client.get_messages(
            channel,
            limit=messages_count,
            filter=telethon.tl.types.InputMessagesFilterMusic(),
        )

        # Tri par ID croissant
        messages = sorted(messages, key=lambda m: m.id)

        # Dictionnaire pour stocker les morceaux valides
        musics = {}

        for msg in messages:
            if msg.media and msg.media.document:
                attrs = msg.media.document.attributes
                file_name = None
                title = None
                performer = None

                for attr in attrs:
                    if hasattr(attr, 'file_name'):
                        file_name = attr.file_name
                    if hasattr(attr, 'title'):
                        title = attr.title
                    if hasattr(attr, 'performer'):
                        performer = attr.performer

                print("------------")
                print(f"Message ID: {msg.id}")
                if title and performer:
                    print(f"Titre: {title}")
                    print(f"Artiste: {performer}")
                    musics[str(msg.id)] = {
                        "title": title,
                        "artist": performer
                    }
                elif file_name:
                    print(f"Nom de fichier (fallback): {file_name}")
                else:
                    print("Aucune info détectée")

        # Sauvegarde dans un fichier JSON
        with open("musics.json", "w", encoding="utf-8") as f:
            json.dump(musics, f, indent=2, ensure_ascii=False)

        print(f"Fetched {len(messages)} music messages.")
        print(f"Saved {len(musics)} valid music entries to musics.json.")
        
    async with telethon_client:
        await fetch_messages_and_profile()


def create_new_playlist(telegram_channel_username):
    '''
    create new playlist for channel and set title, description and image for it
    '''
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