from youtube_transcript_api import YouTubeTranscriptApi
import re

# List of video IDs you want to test (you can add more)
test_ids = [
    "0ZZzhJN9rtM", "NiTcvoFL4es", "c1mKmeE77Zk", 
    "tFpp3F98aVQ", "k3AqQzW3cGI", "GdXvzeCBtM4",
    "lrNuEVPjQwM", "YsDkQoJSCb0", "nfoPPwKpEIQ", 
    "3ILAWIQ969U"  # add more if you have them
]

# You can also add any other IDs you find on the channel

def has_transcript(vid):
    try:
        YouTubeTranscriptApi.get_transcript(vid)
        return True
    except Exception:
        return False

print("Checking transcripts...")
working = []
for vid in test_ids:
    if has_transcript(vid):
        working.append(vid)
        print(f"✅ {vid} has transcript")
    else:
        print(f"❌ {vid} no transcript")

print("\n===== WORKING VIDEO IDs =====")
print("\n".join(working))