import requests
import xml.etree.ElementTree as ET
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

CHANNEL_HANDLE = "muhammadirfanmalik"

def get_channel_id():
    ydl_opts = {'quiet': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/@{CHANNEL_HANDLE}", download=False)
        return info.get('channel_id')

def get_video_ids_from_rss(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch RSS: {response.status_code}")
    root = ET.fromstring(response.text)
    ns = {'yt': 'http://www.youtube.com/xml/schemas/2015'}
    entries = root.findall('entry')
    video_ids = []
    for entry in entries:
        video_id = entry.find('yt:videoId', ns)
        if video_id is not None:
            video_ids.append(video_id.text)
    return video_ids

def has_transcript(vid):
    try:
        YouTubeTranscriptApi.get_transcript(vid)
        return True
    except Exception:
        return False

print("🔄 Fetching channel ID...")
channel_id = get_channel_id()
if not channel_id:
    raise Exception("Could not get channel ID.")
print(f"✅ Channel ID: {channel_id}")

print("🔄 Fetching video IDs from RSS feed...")
video_ids = get_video_ids_from_rss(channel_id)
print(f"Found {len(video_ids)} videos. Testing for transcripts...")

working = []
for vid in video_ids:
    if has_transcript(vid):
        working.append(vid)
        print(f"✅ {vid} has transcript")

print(f"\n🎯 Found {len(working)} videos with transcripts.")

if working:
    selected = working[:10]
    print("Selected 10 working video IDs:")
    for vid in selected:
        print(f"   https://youtu.be/{vid}")
    with open("../data/video_ids.txt", "w") as f:
        for vid in selected:
            f.write(f"https://youtu.be/{vid}\n")
    print("\n✅ Updated data/video_ids.txt with the first 10 working videos.")
else:
    print("\n❌ No videos with transcripts found.")
