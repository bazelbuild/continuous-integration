import os
import pickle
import time
import numpy as np
from google import genai
from typing import List, Dict
from google.cloud import storage

# Cloud Storage Configuration
GCS_BUCKET_NAME = os.environ.get("RAG_MEMORY_BUCKET", "gtech-rmi-dev-rag-memory")
GCS_FILE_NAME = "native_store.pkl"
LOCAL_TMP_FILE = "/tmp/native_store.pkl"

# 1. Initialize Google Gen AI Client once at module level
# (Secrets are injected by cli.py)
client = genai.Client()

def get_embedding(text: str) -> List[float]:
    """Uses Google's native embedding model."""
    try:
        response = client.models.embed_content(
            model="models/gemini-embedding-2",
            contents=text
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        return []

def load_db() -> List[Dict]:
    """Loads the database from Google Cloud Storage."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(GCS_FILE_NAME)

        if blob.exists():
            blob.download_to_filename(LOCAL_TMP_FILE)
            with open(LOCAL_TMP_FILE, 'rb') as f:
                return pickle.load(f)
        return []
    except Exception as e:
        print(f"⚠️ Could not load DB from GCS: {e}")
        return []

def save_db(db: List[Dict]):
    """Saves the database to Google Cloud Storage."""
    try:
        with open(LOCAL_TMP_FILE, 'wb') as f:
            pickle.dump(db, f)

        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(GCS_FILE_NAME)
        blob.upload_from_filename(LOCAL_TMP_FILE)
        print(f"💾 Memory saved to GCS: gs://{GCS_BUCKET_NAME}/{GCS_FILE_NAME}")
    except Exception as e:
        print(f"❌ Error saving DB to GCS: {e}")
def search_docs(query: str, top_k: int = 3) -> str:
    """
    Retriever tool: Searches documentation using native cosine similarity.
    100% Google-native approach.
    """
    print(f"🔍 RAG (Native): Searching for context: {query}")
    db = load_db()
    if not db:
        return "No documentation found in knowledge base."
    
    query_emb_list = get_embedding(query)
    if not query_emb_list:
        return "Error generating query embedding."
        
    query_emb = np.array(query_emb_list)
    
    similarities = []
    for doc in db:
        doc_emb = np.array(doc['embedding'])
        norm_product = np.linalg.norm(query_emb) * np.linalg.norm(doc_emb)
        sim = np.dot(query_emb, doc_emb) / norm_product if norm_product != 0 else 0
        similarities.append(sim)
    
    # Get indices of top results
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        results.append(f"Source: {db[idx].get('file_path', 'unknown')}\nContent: {db[idx]['text']}")
    
    print(f"✅ RAG: Found {len(results)} relevant snippets.")
    return "\n\n---\n\n".join(results)

def upsert_merged_doc(file_path: str, content: str, source_url: str):
    """
    Self-Learning: Updates the native store with merged content.
    """
    db = load_db()
    embedding = get_embedding(content)
    
    new_doc = {
        "file_path": file_path,
        "text": content,
        "embedding": embedding,
        "metadata": {
            "source_url": source_url,
            "status": "merged",
            "timestamp": time.time()
        }
    }
    
    # Simple deduplication by path
    db = [d for d in db if d.get('file_path') != file_path]
    db.append(new_doc)
    save_db(db)
    print(f"✅ RAG (Native): Knowledge base updated for {file_path}")

def upsert_style_lesson(topic: str, lesson_text: str):
    """
    Saves a writing style lesson using native embeddings.
    """
    db = load_db()
    embedding = get_embedding(lesson_text)
    
    lesson_id = f"lesson_{topic}"
    new_lesson = {
        "file_path": lesson_id,
        "text": lesson_text,
        "embedding": embedding,
        "metadata": {
            "type": "style_lesson",
            "topic": topic,
            "timestamp": time.time()
        }
    }
    
    updated_db = [d for d in db if d.get('file_path') != lesson_id]
    updated_db.append(new_lesson)
    
    save_db(updated_db)
    print(f"🎓 RAG (Native): Learned a new style lesson: {topic}")

def bulk_ingest(docs_dir: str):
    """Initial population of the knowledge base."""
    print(f"🚀 RAG (Native): Starting bulk ingestion from {docs_dir}")
    db = []
    
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith((".md", ".mdx")):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r") as f:
                        content = f.read()
                    if not content.strip(): continue
                    
                    print(f"  📄 Processing {file}...")
                    embedding = get_embedding(content)
                    db.append({
                        "file_path": file_path,
                        "text": content,
                        "embedding": embedding
                    })
                    time.sleep(0.2) # Modest rate limit safety
                except Exception as e:
                    print(f"  ❌ Failed to process {file}: {e}")
                    
    save_db(db)
    print(f"✅ RAG (Native): Initialized with {len(db)} documents.")
