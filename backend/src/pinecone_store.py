from pinecone import DenseVectorQuery, Pinecone, ServerlessSpec
import config
import time

NAMESPACE = "youtube"

pc = Pinecone(api_key=config.PINECONE_API_KEY)

def create_index_if_not_exists():
    existing = pc.list_indexes().names()
    if config.PINECONE_INDEX not in existing:
        pc.create_index(
            name=config.PINECONE_INDEX,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=config.PINECONE_ENVIRONMENT.split('-')[0])
        )
        while not pc.describe_index(config.PINECONE_INDEX).status['ready']:
            time.sleep(1)

def get_index():
    return pc.Index(config.PINECONE_INDEX)

def upsert_vectors(vectors):
    index = get_index()
    documents = []
    for vector_id, embedding, metadata in vectors:
        documents.append({
            "_id": vector_id,
            "embedding": embedding,
            **metadata,
        })
    index.documents.upsert(namespace=NAMESPACE, documents=documents)

def query_vectors(query_embedding, top_k=config.TOP_K, video_id=None):
    index = get_index()
    search_options = {
        "namespace": NAMESPACE,
        "score_by": [DenseVectorQuery(field="embedding", values=query_embedding)],
        "top_k": top_k,
        "include_fields": ["video_id", "video_url", "start_time", "text", "title", "channel", "description"],
    }
    if video_id:
        search_options["filter"] = {"video_id": {"$eq": video_id}}
    results = index.documents.search(**search_options)
    matches = []
    for match in results.matches:
        data = match.to_dict() if hasattr(match, "to_dict") else match.__dict__
        fields = {
            key: data[key]
            for key in ("video_id", "video_url", "start_time", "text", "title", "channel", "description")
            if key in data
        }
        matches.append({
            "id": data.get("_id", data.get("id", "")),
            "score": data.get("_score", data.get("score", 0.0)),
            "metadata": fields,
        })
    return matches