from openai import OpenAI
import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

def embed_texts(texts):
    response = client.embeddings.create(
        model=config.EMBEDDING_MODEL,
        input=texts
    )
    return [item.embedding for item in response.data]