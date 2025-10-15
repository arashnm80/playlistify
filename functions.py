from config import *
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time

# Thread-safe lock for progress tracking
progress_lock = Lock()
found_tracks = []
processed_count = 0

def search_song_thread_safe(song, similarity_threshold):
    """
    Thread-safe function to search for a single song with retry logic
    Returns the track URI if found with sufficient similarity
    """
    global processed_count
    
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            # Add small delay between requests to avoid rate limiting
            time.sleep(0.1)
            
            result = sp.search(q=song, limit=1, type="track")
            tracks = result.get("tracks", {}).get("items", [])
            
            if tracks:
                found_track = tracks[0]
                found_track_name = found_track["name"]
                found_track_artists = ", ".join([artist["name"] for artist in found_track["artists"]])
                found_track_full = f"{found_track_name} - {found_track_artists}"
                
                # Calculate similarity score
                similarity_score = SequenceMatcher(None, song.lower(), found_track_full.lower()).ratio()
                
                if similarity_score >= similarity_threshold:
                    with progress_lock:
                        found_tracks.append(found_track["uri"])
                        processed_count += 1
                        if processed_count % 50 == 0:  # Reduced frequency
                            print(f"[*] Processed {processed_count} songs, found {len(found_tracks)} matches...")
                    return found_track["uri"], song, found_track_full, similarity_score
                else:
                    with progress_lock:
                        processed_count += 1
                        if processed_count % 50 == 0:
                            print(f"[*] Processed {processed_count} songs, found {len(found_tracks)} matches...")
                    return None, song, found_track_full, similarity_score
            else:
                with progress_lock:
                    processed_count += 1
                    if processed_count % 50 == 0:
                        print(f"[*] Processed {processed_count} songs, found {len(found_tracks)} matches...")
                return None, song, None, 0.0
                
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                # Rate limited - wait longer before retry
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"⚠️  Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
            else:
                # Other error - don't retry
                break
    
    # If we get here, all retries failed
    with progress_lock:
        processed_count += 1
        print(f"❌ Failed to search '{song}' after {max_retries} attempts")
    return None, song, None, 0.0

def create_new_playlist(telegram_channel_username):
    '''
    create new playlist for channel and set title, description and image for it
    '''
    # Read channel info from musics.json to get proper title and username
    playlist_name = f"t.me/{telegram_channel_username}"  # Default fallback
    playlist_description = "automatically generated playlist from tracks in telegram channel. developer: Arashnm80"
    
    try:
        with open('musics.json', 'r', encoding='utf-8') as f:
            musics_data = json.load(f)
        
        if 'channel_info' in musics_data:
            channel_info = musics_data['channel_info']
            channel_title = channel_info.get('title', '')
            channel_username = channel_info.get('username', telegram_channel_username)
            
            # Create playlist name from title and username
            if channel_title and channel_username:
                playlist_name = f"{channel_title} (@{channel_username})"
            elif channel_title:
                playlist_name = channel_title
            elif channel_username:
                playlist_name = f"@{channel_username}"
            
            # Create description with channel info
            playlist_description = f"Automatically generated playlist from @{channel_username} - {channel_title if channel_title else 'Telegram Channel'}"
            
            print(f"📺 Creating playlist: {playlist_name}")
            print(f"📝 Description: {playlist_description}")
            
    except Exception as e:
        print(f"⚠️  Could not read channel info from musics.json: {e}")
        print(f"📺 Using default playlist name: {playlist_name}")
    
    # Création de la playlist
    playlist = sp.user_playlist_create(
        user=user_id,
        name=playlist_name,
        description=playlist_description,
        public=True,  # ou False pour une playlist privée
    )

    # get id of generated playlist
    playlist_id = playlist["id"]

    # set image for playlist
    try:
        # Try channel_profile.png first, then fallback to image.png
        image_path = None
        for path in ["image.png"]:
            if os.path.exists(path):
                image_path = path
                break
        
        if image_path:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read())
            sp.playlist_upload_cover_image(playlist_id, image_data)
            print(f"✅ Playlist cover image uploaded successfully from {image_path}")
        else:
            print("⚠️  No cover image found (channel_profile.png or image.png). Playlist created without cover image.")
    except Exception as e:
        print(f"⚠️  Error uploading cover image: {e}")

    # Affichage de l'ID de la playlist créée
    print("Playlist ID:", playlist_id)

    # output to be used by the rest of the code
    return playlist_id

def set_playlist_tracks(playlist_id):
    '''
    set tracks for given playlist id based on musics.json file
    matches songs based on similarity threshold using multithreading for speed
    '''
    global found_tracks, processed_count
    
    # Reset global variables
    found_tracks = []
    processed_count = 0
    
    # Charger les données JSON depuis le fichier
    with open('musics.json', 'r') as f:
        musics_json = json.load(f)

    # Handle both old format (dict) and new format (with audio_files array)
    if 'audio_files' in musics_json:
        # New format from telegram_music_scraper_with_profile.py
        audio_files = musics_json['audio_files']
        song_names = []
        for audio_file in audio_files:
            if audio_file.get('title') and audio_file.get('artist'):
                song_names.append(f"{audio_file['title']} - {audio_file['artist']}")
    else:
        # Old format (dict with song IDs as keys)
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

    total_songs = len(song_names)
    print(f"🎵 Processing {total_songs} songs with multithreading...")
    
    # Use fewer threads to avoid rate limiting
    max_workers = min(5, total_songs)  # Reduced from 20 to 5 to avoid rate limits
    print(f"⚡ Using {max_workers} threads to avoid rate limiting")
    
    # Use multithreading to search for songs
    track_uris = []
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all search tasks
        future_to_song = {
            executor.submit(search_song_thread_safe, song, SIMILARITY_THRESHOLD): song 
            for song in song_names
        }
        
        # Process completed tasks
        for future in as_completed(future_to_song):
            song = future_to_song[future]
            try:
                track_uri, original_song, found_track_full, similarity_score = future.result()
                
                if track_uri:
                    track_uris.append(track_uri)
                    if similarity_score >= 0.8:  # Only show high-confidence matches to reduce spam
                        print(f"✅ Found: {original_song} (Similarity: {similarity_score:.2%})")
                elif found_track_full and similarity_score < SIMILARITY_THRESHOLD:
                    # Only show low similarity for first 20 to reduce spam
                    if len(track_uris) < 20:
                        print(f"⚠️ Low match: {original_song} → {found_track_full} (Similarity: {similarity_score:.2%})")
                        
            except Exception as e:
                print(f"❌ Error processing '{song}': {e}")

    elapsed_time = time.time() - start_time
    print(f"\n⚡ Multithreaded search completed in {elapsed_time:.1f} seconds")
    print(f"🎯 Found {len(track_uris)} matching tracks out of {total_songs} songs")

    # Ajouter les morceaux trouvés à la playlist par lots de 100 maximum
    if track_uris:
        print(f"📝 Adding {len(track_uris)} tracks to playlist...")
        # Diviser les pistes en lots de 100 maximum
        batch_size = 100
        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i:i+batch_size]
            sp.playlist_add_items(playlist_id, batch)
            print(f"✅ Batch {i//batch_size + 1}: {len(batch)} tracks added to playlist.")
            # Add 2 second pause between batches to avoid rate limiting
            time.sleep(2)
        
        print(f"🎉 Total: {len(track_uris)} tracks successfully added to playlist!")
    else:
        print("⚠️ No matching tracks found to add.")