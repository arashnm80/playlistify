from functions import *

if __name__ == "__main__":
    # targeted telegram channel username (without beginnning "@" + case sensitive)
    telegram_channel_username = "alaskaandtea"

    # create new playlist and save its id
    playlist_id = create_new_playlist(telegram_channel_username)

    # set tracks for the created playlist
    set_playlist_tracks(playlist_id)

    print(f"\n\nchannel username: @{telegram_channel_username}")
    print(f"playlist link: https://open.spotify.com/playlist/{playlist_id}")