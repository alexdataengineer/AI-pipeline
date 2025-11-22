"""
Manual CV ingestion script.
Run this to ingest the CV into Pinecone without using Airflow.

Usage:
    python ingest_cv.py
"""
from app.pdf_loader import process_pdf_to_chunks
from app.embeddings import embed_texts
from app.rag import get_pinecone_client, ensure_pinecone_index
from config.settings import settings


def main():
    """Main ingestion function."""
    print("=" * 60)
    print("CV Ingestion Pipeline")
    print("=" * 60)
    
    # Step 1: Load and chunk PDF
    print(f"\n[Step 1] Loading PDF from: {settings.cv_pdf_path}")
    chunks = process_pdf_to_chunks()
    print(f"✓ Created {len(chunks)} chunks from PDF")
    
    # Step 2: Create embeddings
    print(f"\n[Step 2] Creating embeddings for {len(chunks)} chunks...")
    texts = [chunk['text'] for chunk in chunks]
    
    # Create embeddings in batches
    batch_size = 100
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_embeddings = embed_texts(batch_texts)
        all_embeddings.extend(batch_embeddings)
        print(f"  ✓ Embedded batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")
    
    print(f"✓ Created {len(all_embeddings)} embeddings")
    
    # Step 3: Ensure Pinecone index exists
    print(f"\n[Step 3] Ensuring Pinecone index exists...")
    ensure_pinecone_index()
    
    # Step 4: Upsert to Pinecone
    print(f"\n[Step 4] Upserting vectors to Pinecone...")
    pc = get_pinecone_client()
    index = pc.Index(settings.pinecone_index_name)
    
    # Prepare vectors
    vectors = []
    for chunk, embedding in zip(chunks, all_embeddings):
        vectors.append({
            'id': chunk['id'],
            'values': embedding,
            'metadata': chunk['metadata']
        })
    
    # Upsert in batches
    upsert_batch_size = 100
    for i in range(0, len(vectors), upsert_batch_size):
        batch_vectors = vectors[i:i + upsert_batch_size]
        index.upsert(vectors=batch_vectors)
        print(f"  ✓ Upserted batch {i // upsert_batch_size + 1}/{(len(vectors) + upsert_batch_size - 1) // upsert_batch_size}")
    
    print(f"\n✓ Successfully upserted {len(vectors)} vectors to Pinecone index: {settings.pinecone_index_name}")
    print("\n" + "=" * 60)
    print("Ingestion complete! You can now start the FastAPI app to query your CV.")
    print("=" * 60)


if __name__ == "__main__":
    main()

