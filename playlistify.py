from functions import *
import json

if __name__ == "__main__":
    print("Playlistify - Spotify Playlist Creator")
    print("=" * 50)
    print()
    
    # Check if musics.json exists
    try:
        with open('musics.json', 'r', encoding='utf-8') as f:
            musics_data = json.load(f)
        
        if 'channel_info' in musics_data:
            channel_info = musics_data['channel_info']
            telegram_channel_username = channel_info.get('username', '')
            channel_title = channel_info.get('title', '')
            
            print(f"Found channel: {channel_title} (@{telegram_channel_username})")
        else:
            print("No channel info found in musics.json")
            telegram_channel_username = ""
            channel_title = ""
            
    except FileNotFoundError:
        print("Error: musics.json not found!")
        print("Please run music_scraper.py first to extract audio metadata.")
        print("Usage: python music_scraper.py")
        exit(1)
    except Exception as e:
        print(f"Error reading musics.json: {e}")
        exit(1)
    
    print("\nCreating Spotify playlist...")
    print("=" * 50)
    
    # Create new playlist and save its id
    playlist_id = create_new_playlist(telegram_channel_username)

    # Set tracks for the created playlist
    set_playlist_tracks(playlist_id)

    print(f"\n\nPlaylist creation completed!")
    if channel_title:
        print(f"Channel: {channel_title} (@{telegram_channel_username})")
    else:
        print(f"Channel: @{telegram_channel_username}")
    print(f"Playlist link: https://open.spotify.com/playlist/{playlist_id}")