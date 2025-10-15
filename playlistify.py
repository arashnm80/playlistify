from functions import *
import json

if __name__ == "__main__":
    print("🎵 Starting playlist creation process...")
    print("=" * 50)
    
    # Read channel info from musics.json
    telegram_channel_username = ""  # Default fallback
    channel_title = ""
    
    try:
        with open('musics.json', 'r', encoding='utf-8') as f:
            musics_data = json.load(f)
        
        if 'channel_info' in musics_data:
            channel_info = musics_data['channel_info']
            telegram_channel_username = channel_info.get('username', telegram_channel_username)
            channel_title = channel_info.get('title', '')
            
            print(f"📺 Found channel: {channel_title} (@{telegram_channel_username})")
        else:
            print(f"⚠️  No channel info found in musics.json, using default: @{telegram_channel_username}")
            
    except Exception as e:
        print(f"⚠️  Could not read musics.json: {e}")
        print(f"📺 Using default channel: @{telegram_channel_username}")
    
    # create new playlist and save its id
    playlist_id = create_new_playlist(telegram_channel_username)

    # set tracks for the created playlist
    set_playlist_tracks(playlist_id)

    print(f"\n\n🎉 Playlist creation completed!")
    if channel_title:
        print(f"📺 Channel: {channel_title} (@{telegram_channel_username})")
    else:
        print(f"📺 Channel: @{telegram_channel_username}")
    print(f"🔗 Playlist link: https://open.spotify.com/playlist/{playlist_id}")