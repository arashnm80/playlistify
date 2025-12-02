from functions import *

# Run the bot asynchronously
async def fetch_channel_data(telegram_channel_username):

    # Create async telethon client with telegram app api
    telethon_client = telethon.TelegramClient(session_name, TELEGRAM_APP_API_ID, TELEGRAM_APP_API_HASH, proxy=warp_proxies_tuple)
    await telethon_client.start()

    # channel username without "@" , case sensivity doesn't matter
    await fetch_channel_musics_and_profile(telethon_client, MAX_MESSAGES_COUNT, telegram_channel_username)


if __name__ == "__main__":
    # targeted telegram channel username (without beginnning "@" + case sensitive for good look only)
    telegram_channel_username = "songofsalvation"

    # fetch telegram channel musics and profile
    asyncio.run(fetch_channel_data(telegram_channel_username))

    # create new playlist and save its id
    playlist_id = create_new_playlist(telegram_channel_username)

    # set tracks for the created playlist
    set_playlist_tracks(playlist_id)

    print(f"\n\nchannel username: @{telegram_channel_username}")
    print(f"playlist link: https://open.spotify.com/playlist/{playlist_id}")