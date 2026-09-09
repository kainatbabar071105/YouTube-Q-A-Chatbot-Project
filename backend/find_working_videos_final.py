import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import yt_dlp

CHANNEL_HANDLE = "muhammadirfanmalik"
VIDEO_COUNT = 10
OUTPUT_FILE = Path(__file__).resolve().parent / "data" / "video_ids.txt"

def get_channel_and_playlist_id():
    """Get channel ID and uploads playlist ID using yt-dlp."""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'ignoreerrors': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/@{CHANNEL_HANDLE}", download=False)
        channel_id = info.get('channel_id')
        if not channel_id:
            # fallback: try to get from channel url
            channel_id = info.get('uploader_id')
        # The uploads playlist is usually "UU" + channel_id[2:] if channel_id starts with "UC"
        if channel_id and channel_id.startswith('UC'):
            uploads_playlist = "UU" + channel_id[2:]
        else:
            # maybe it's already the playlist ID?
            uploads_playlist = channel_id  # fallback
        return channel_id, uploads_playlist

def fetch_video_ids_from_rss(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"RSS fetch failed: {response.status_code} for {url}")
    root = ET.fromstring(response.text)
    ns = {'yt': 'http://www.youtube.com/xml/schemas/2015'}
    entries = root.findall('entry')
    video_ids = []
    for entry in entries:
        video_id = entry.find('yt:videoId', ns)
        if video_id is not None:
            video_ids.append(video_id.text)
    return video_ids

print("🔄 Fetching channel info...")
channel_id, playlist_id = get_channel_and_playlist_id()
print(f"Channel ID: {channel_id}")
print(f"Uploads Playlist ID: {playlist_id}")

video_ids = []
# Try different RSS endpoints
urls = [
    f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
    f"https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}",
    f"https://www.youtube.com/feeds/videos.xml?user={CHANNEL_HANDLE}"   # unlikely
]

for url in urls:
    try:
        print(f"Trying RSS: {url}")
        ids = fetch_video_ids_from_rss(url)
        if ids:
            video_ids = ids
            print(f"✅ Got {len(ids)} videos from {url}")
            break
    except Exception as e:
        print(f"  Failed: {e}")

# If RSS failed, use yt-dlp with playlist extraction.
if not video_ids:
    print("RSS failed. Using yt-dlp to extract the latest videos directly...")

    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'playlistend': VIDEO_COUNT,
        'ignoreerrors': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/@{CHANNEL_HANDLE}/videos",
            download=False,
        )
        entries = (info or {}).get('entries', [])
        video_ids = [entry['id'] for entry in entries if entry and entry.get('id')]
    print(f"Found {len(video_ids)} videos via yt-dlp.")

if not video_ids:
    print("❌ Could not retrieve any video IDs.")
    exit()

selected = video_ids[:VIDEO_COUNT]
print(f"\n🎯 Selected the latest {len(selected)} videos:")
for vid in selected:
    print(f"   https://youtu.be/{vid}")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT_FILE.open("w", encoding="utf-8") as file:
    for vid in selected:
        file.write(f"https://youtu.be/{vid}\n")
print(f"\n✅ Updated {OUTPUT_FILE}.")