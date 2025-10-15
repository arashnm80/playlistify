
"""
Telegram Audio Metadata Scraper - JSON Export + Channel Profile Picture
Extracts audio metadata (artist, title, file info) and saves to JSON file
Also downloads channel profile picture
"""

import json
from telethon.sync import TelegramClient
from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeFilename
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# CONFIGURATION
API_ID = os.getenv('TELEGRAM_API_ID')  # Get from https://my.telegram.org
API_HASH = os.getenv('TELEGRAM_API_HASH')  # Get from https://my.telegram.org
PHONE = os.getenv('TELEGRAM_PHONE')  # e.g., +1234567890
CHANNEL_USERNAME = os.getenv('TELEGRAM_CHANNEL_USERNAME')  # Target channel username (without @)
OUTPUT_JSON = 'musics.json'
PROFILE_PIC_PATH = 'image.png'
MESSAGE_LIMIT = int('10000')  # Number of messages to scan (set high to get all music)

# Validate required environment variables
if not API_ID or not API_HASH or not PHONE:
    print("Error: Missing required Telegram credentials in .env file")
    print("Required variables:")
    print("  - TELEGRAM_API_ID")
    print("  - TELEGRAM_API_HASH") 
    print("  - TELEGRAM_PHONE")
    exit(1)

# Check if channel username is provided, if not ask user
if not CHANNEL_USERNAME:
    print("Telegram Audio Metadata Scraper")
    print("=" * 50)
    print()
    
    while True:
        channel_username = input("Enter Telegram channel username (without @): ").strip()
        if channel_username:
            # Remove @ if user included it
            if channel_username.startswith('@'):
                channel_username = channel_username[1:]
            CHANNEL_USERNAME = channel_username
            break
        print("Please enter a valid channel username.")
    
    print(f"\nSelected channel: @{CHANNEL_USERNAME}")
    print("=" * 50)


# TELEGRAM METADATA EXTRACTOR
async def extract_audio_metadata():
    """
    Connect to Telegram and extract audio metadata WITHOUT downloading
    Also downloads channel profile picture
    """
    audio_metadata_list = []
    channel_info = {}

    # Initialize Telegram client
    async with TelegramClient('music_metadata_session', API_ID, API_HASH) as client:
        print("Connected to Telegram")
        me = await client.get_me()
        print(f"Logged in as: {me.first_name}")

        # Get the target channel
        channel = await client.get_entity(CHANNEL_USERNAME)
        print(f"Scanning channel: {channel.title}")

        # Store channel information
        channel_info = {
            'title': channel.title,
            'username': channel.username,
            'id': channel.id,
            'description': getattr(channel, 'about', ''),
            'subscribers': getattr(channel, 'participants_count', None)
        }

        # Download channel profile picture
        print("Downloading channel profile picture...")
        try:
            profile_pic_path = await client.download_profile_photo(
                channel, 
                file=PROFILE_PIC_PATH
            )
            if profile_pic_path:
                print(f"Profile picture saved to: {profile_pic_path}")
                channel_info['profile_picture'] = profile_pic_path
            else:
                print("No profile picture available for this channel")
                channel_info['profile_picture'] = None
        except Exception as e:
            print(f"Error downloading profile picture: {e}")
            channel_info['profile_picture'] = None

        print(f"Searching for audio files (scanning up to {MESSAGE_LIMIT} messages)...")
        print("=" * 80)

        audio_count = 0
        message_count = 0

        # Iterate through messages
        async for message in client.iter_messages(channel, limit=MESSAGE_LIMIT):
            message_count += 1
            
            # Progress indicator every 100 messages
            if message_count % 100 == 0:
                print(f"Scanned {message_count} messages, found {audio_count} audio files...")
            # Check if message contains audio or audio document
            if message.audio or (message.document and message.document.mime_type and 
                                'audio' in message.document.mime_type):

                audio_count += 1

                # Initialize metadata dictionary with clean structure
                metadata = {
                    'artist': None,
                    'title': None,
                    'file_name': None,
                    'duration_seconds': None,
                    'file_size_mb': None,
                    'mime_type': None,
                    'message_id': message.id,
                    'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                    'channel': channel.title,
                    'caption': message.text or ''
                }

                # Extract from message.audio
                if message.audio:
                    audio = message.audio
                    metadata['mime_type'] = audio.mime_type
                    metadata['file_size_mb'] = round(audio.size / (1024 * 1024), 2)

                    # Get attributes
                    for attr in audio.attributes:
                        if isinstance(attr, DocumentAttributeAudio):
                            metadata['title'] = getattr(attr, 'title', None)
                            metadata['artist'] = getattr(attr, 'performer', None)
                            metadata['duration_seconds'] = getattr(attr, 'duration', None)
                        elif isinstance(attr, DocumentAttributeFilename):
                            metadata['file_name'] = getattr(attr, 'file_name', None)

                # Extract from message.document (audio files sent as documents)
                elif message.document:
                    doc = message.document
                    metadata['mime_type'] = doc.mime_type
                    metadata['file_size_mb'] = round(doc.size / (1024 * 1024), 2)

                    # Get attributes
                    for attr in doc.attributes:
                        if isinstance(attr, DocumentAttributeAudio):
                            metadata['title'] = getattr(attr, 'title', None)
                            metadata['artist'] = getattr(attr, 'performer', None)
                            metadata['duration_seconds'] = getattr(attr, 'duration', None)
                        elif isinstance(attr, DocumentAttributeFilename):
                            metadata['file_name'] = getattr(attr, 'file_name', None)

                # Print metadata to console (only for first 20, then summary)
                if audio_count <= 20:
                    print(f"[{audio_count}] {metadata['artist'] or 'Unknown Artist'} - {metadata['title'] or 'Unknown Title'}")
                    print(f"    File: {metadata['file_name'] or 'N/A'} | Size: {metadata['file_size_mb']} MB | Duration: {metadata['duration_seconds']}s")
                elif audio_count % 50 == 0:  # Show progress every 50 audio files
                    print(f"Found {audio_count} audio files so far...")

                audio_metadata_list.append(metadata)

        print("\n" + "=" * 80)
        print(f"Scanned {message_count} messages and found {audio_count} audio files")

    return audio_metadata_list, channel_info


# MAIN EXECUTION
if __name__ == '__main__':
    print("=" * 80)
    print("Telegram Audio Metadata Scraper + Profile Picture Downloader")
    print("=" * 80)
    print()

    # Run the metadata extractor
    audio_data, channel_info = asyncio.run(extract_audio_metadata())

    # Create structured JSON output
    output = {
        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'channel_info': channel_info,
        'total_files': len(audio_data),
        'audio_files': audio_data
    }

    # Save metadata to JSON with proper formatting
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nMetadata saved to: {OUTPUT_JSON}")
    if channel_info.get('profile_picture'):
        print(f"Profile picture saved to: {channel_info['profile_picture']}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Channel: {channel_info['title']}")
    print(f"Username: @{channel_info['username']}")
    if channel_info.get('subscribers'):
        print(f"Subscribers: {channel_info['subscribers']}")
    print(f"\nTotal audio files: {len(audio_data)}")

    # Count files with metadata
    with_title = sum(1 for a in audio_data if a['title'])
    with_artist = sum(1 for a in audio_data if a['artist'])
    complete = [a for a in audio_data if a['title'] and a['artist']]

    print(f"Files with title:  {with_title} ({round(with_title/len(audio_data)*100 if audio_data else 0, 1)}%)")
    print(f"Files with artist: {with_artist} ({round(with_artist/len(audio_data)*100 if audio_data else 0, 1)}%)")
    print(f"Complete metadata: {len(complete)} ({round(len(complete)/len(audio_data)*100 if audio_data else 0, 1)}%)")

    # Show sample of files with complete metadata
    if complete:
        print(f"\nSample tracks with complete metadata:")
        for audio in complete[:10]:
            print(f"  • {audio['artist']} - {audio['title']}")

    print(f"\nAll data exported successfully!")
    print(f"    - Metadata: {OUTPUT_JSON}")
    if channel_info.get('profile_picture'):
        print(f"    - Profile picture: {channel_info['profile_picture']}")
    
    # Ask user if they want to create Spotify playlist
    print("\n" + "=" * 80)
    while True:
        create_playlist = input("Do you want to create a Spotify playlist now? (y/n): ").strip().lower()
        if create_playlist in ['y', 'yes', 'n', 'no']:
            break
        print("Please enter 'y' for yes or 'n' for no.")
    
    if create_playlist in ['y', 'yes']:
        print("\nCreating Spotify playlist...")
        print("=" * 50)
        
        try:
            import subprocess
            import sys
            result = subprocess.run([sys.executable, 'playlistify.py'], check=True)
            print("Spotify playlist created successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error creating Spotify playlist: {e}")
        except FileNotFoundError:
            print("Error: playlistify.py not found. Please make sure the file exists.")
        except Exception as e:
            print(f"Unexpected error: {e}")
    else:
        print("You can create a Spotify playlist later by running: python playlistify.py")
