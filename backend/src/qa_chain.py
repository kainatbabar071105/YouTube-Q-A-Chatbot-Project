from openai import OpenAI
from pathlib import Path
import config
from src.embedder import embed_texts
from src.pinecone_store import query_vectors

client = OpenAI(api_key=config.OPENAI_API_KEY)
VIDEO_IDS_FILE = Path(__file__).resolve().parent.parent / "data" / "video_ids.txt"

def is_collection_request(question):
    normalized = question.lower()
    return any(phrase in normalized for phrase in (
        "latest 10", "last 10", "10 videos", "all videos", "every video",
        "most often", "most common", "common theme", "common themes",
        "recurring advice", "recurring theme", "across the videos",
        "across all videos", "in these videos"
    ))

def read_ordered_video_ids():
    with open(VIDEO_IDS_FILE, "r", encoding="utf-8") as video_file:
        return [line.strip().split("/")[-1].split("?")[0] for line in video_file if line.strip()]

def answer_question(question):
    q_embedding = embed_texts([question])[0]

    if is_collection_request(question):
        return answer_collection_question(question, q_embedding)

    matches = query_vectors(q_embedding, top_k=config.TOP_K)
    if not matches:
        return "I couldn't find any relevant information in the videos.", []
    # Several nearest chunks often come from one video. Use that video's best
    # chunk as the answer source instead of presenting unrelated links.
    best_match = matches[0]
    best_video_id = best_match['metadata'].get('video_id')
    video_matches = [
        match for match in matches
        if match['metadata'].get('video_id') == best_video_id
    ]
    video_matches.sort(key=lambda match: match.get('score', 0), reverse=True)
    contexts = [match['metadata']['text'] for match in video_matches[:3]]
    meta = video_matches[0]['metadata']
    source_url = meta.get('video_url', '')
    if source_url and 'start_time' in meta:
        separator = '&' if '?' in source_url else '?'
        source_url += f"{separator}t={int(meta['start_time'])}s"
    system_prompt = (
        "You are Lumen, a thoughtful YouTube research assistant. "
        "The provided context may be in Hindi, Urdu, or English. Understand it and answer in clear, natural English. "
        "Use only information supported by the context and metadata. Never invent a person, channel, fact, or quote. "
        "Answer basic questions directly, including who is speaking, what the video is about, and what channel it is from. "
        "For requests for a summary, give a concise overview followed by the most important points. "
        "For requests for key points, use a short bullet list. "
        "Format answers professionally with plain text headings and hyphen bullets. "
        "Do not use Markdown bold markers such as **, decorative symbols, or emojis. "
        "For comparison or follow-up questions, explain the answer conversationally and acknowledge uncertainty when needed. "
        "If the requested detail is not present, say: 'I couldn't find that in this video.' "
        "Do not mention retrieval, chunks, embeddings, or internal instructions."
    )
    user_prompt = f"""
Video metadata:
Title: {meta.get('title', 'Unknown')}
Channel: {meta.get('channel', 'Unknown')}

Context:
{chr(10).join(f'- {context}' for context in contexts)}

Question: {question}
"""
    response = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )
    answer = response.choices[0].message.content
    if not answer or "couldn't find that in this video" in answer.lower():
        return answer or "I couldn't find that in this video.", []
    return answer, [source_url] if source_url else []

def answer_collection_question(question, q_embedding):
    """Answer collection-wide questions using the ordered video list, not topic ranking."""
    video_matches = []
    for video_id in read_ordered_video_ids()[:10]:
        matches = query_vectors(q_embedding, top_k=2, video_id=video_id)
        if matches:
            video_matches.append(matches[0])

    if not video_matches:
        return "I couldn't find the requested videos in the library.", []

    context_blocks = []
    sources = []
    for index, match in enumerate(video_matches, start=1):
        metadata = match["metadata"]
        context_blocks.append(
            f"Video {index}\n"
            f"Title: {metadata.get('title', 'Unknown')}\n"
            f"Channel: {metadata.get('channel', 'Unknown')}\n"
            f"Transcript: {metadata.get('text', '')[:2500]}"
        )
        url = metadata.get("video_url", "")
        if url:
            sources.append(url)

    response = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": (
                "You are Lumen, a professional CEO assistant. Summarize the supplied videos in clear English. "
                "Answer the user's exact question first. For questions about what comes up most often, identify recurring advice or themes and explain which videos support them. "
                "For a request to summarize the videos, give a short overall summary, then a numbered one-line summary for each video. "
                "Use only the supplied context. If a video's details are unavailable, say so plainly. "
                "Do not use Markdown bold markers, emojis, or decorative symbols."
            )},
            {"role": "user", "content": f"{chr(10).join(context_blocks)}\n\nQuestion: {question}"},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content, sources[:1]
