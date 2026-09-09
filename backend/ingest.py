from pathlib import Path

import yt_dlp

from src.transcript_fetcher import extract_video_id, get_transcript
from src.chunker import chunk_transcript
from src.embedder import embed_texts
from src.pinecone_store import create_index_if_not_exists, get_index, upsert_vectors
import config

DATA_FILE = Path(__file__).resolve().parent / "data" / "video_ids.txt"

def read_video_ids(file_path=DATA_FILE):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    return [extract_video_id(line) for line in lines]

def get_video_info(video_id):
    options = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
    return {
        "title": info.get("title") or f"Video {video_id}",
        "channel": info.get("channel") or info.get("uploader") or "Unknown",
        "description": (info.get("description") or "").strip(),
    }

def get_metadata_fallback(video_id, video_info):
    text = f"Title: {video_info['title']}\nChannel: {video_info['channel']}\n\nDescription:\n{video_info['description']}".strip()
    return [{"text": text, "start_time": 0.0}]

def ingest_all():
    print("Creating Pinecone index (if not exists)...")
    create_index_if_not_exists()
    video_ids = read_video_ids()
    print(f"Found {len(video_ids)} videos to process.")
    all_vectors = []
    skipped = 0
    for idx, vid in enumerate(video_ids):
        print(f"Processing {idx+1}/{len(video_ids)}: {vid}")
        try:
            try:
                video_info = get_video_info(vid)
            except Exception:
                video_info = {
                    "title": f"Video {vid}",
                    "channel": "Unknown",
                    "description": "",
                }
            try:
                transcript = get_transcript(vid)
                chunks = chunk_transcript(transcript, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
            except Exception:
                chunks = get_metadata_fallback(vid, video_info)
                print("  Captions unavailable; using video metadata")
            if not chunks:
                print(f"  Skipping {vid}: transcript produced no usable chunks")
                skipped += 1
                continue
            texts = [chunk['text'] for chunk in chunks]
            embeddings = embed_texts(texts)
            for i, chunk in enumerate(chunks):
                vector_id = f"{vid}_{i}"
                metadata = {
                    "video_id": vid,
                    "video_url": f"https://youtu.be/{vid}",
                    "title": video_info["title"],
                    "channel": video_info["channel"],
                    "description": video_info["description"],
                    "start_time": chunk['start_time'],
                    "text": chunk['text']
                }
                all_vectors.append((vector_id, embeddings[i], metadata))
            print(f"  Prepared {len(chunks)} chunks")
        except Exception as error:
            safe_error = str(error).encode("ascii", "backslashreplace").decode("ascii")
            print(f"  Skipping {vid}: {safe_error}")
            skipped += 1
    if all_vectors:
        print(f"Upserting {len(all_vectors)} vectors to Pinecone...")
        batch_size = 100
        for i in range(0, len(all_vectors), batch_size):
            batch = all_vectors[i:i+batch_size]
            upsert_vectors(batch)
        print(f"Ingestion complete. Skipped {skipped} videos.")
        print(f"Pinecone vector count: {get_index().describe_index_stats().total_vector_count}")
    else:
        print(f"No vectors to upsert. Skipped {skipped} videos.")

if __name__ == "__main__":
    ingest_all()