from youtube_transcript_api import YouTubeTranscriptApi
import re

def extract_video_id(url_or_id: str) -> str:
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11})(?:[?&]|$)',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from {url_or_id}")

def get_transcript(video_id: str):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=['ur', 'hi', 'en', 'en-US', 'en-GB']
        )
        return transcript
    except Exception:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return transcript
        except Exception as e:
            raise RuntimeError(f"Could not fetch transcript for {video_id}: {e}")