## guide

### Step 1: Extract Audio Metadata
```bash
python music_scraper.py
```
- Enter Telegram channel username when prompted
- Authenticate with Telegram (first time only)
- Extracts audio metadata and saves to `musics.json`
- Downloads channel profile picture as `image.png`
- Optionally creates Spotify playlist automatically

### Step 2: Create Spotify Playlist
```bash
python playlistify.py
```
- Reads metadata from `musics.json`
- Creates Spotify playlist with channel info
- Uses multithreading for fast track matching
- Supports similarity threshold configuration