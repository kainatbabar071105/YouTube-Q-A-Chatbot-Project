def chunk_transcript(transcript_list, chunk_size=500, overlap=50):
    full_text_parts = []
    time_map = []
    for item in transcript_list:
        words = item['text'].split()
        for w in words:
            full_text_parts.append(w)
            time_map.append(item['start'])
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(full_text_parts), step):
        chunk_words = full_text_parts[i:i+chunk_size]
        if len(chunk_words) < 10:
            continue
        chunk_text = " ".join(chunk_words)
        start_time = time_map[i] if i < len(time_map) else 0.0
        chunks.append({
            "text": chunk_text,
            "start_time": start_time
        })
    return chunks