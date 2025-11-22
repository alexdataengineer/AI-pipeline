"""
Airflow DAG for CV ingestion pipeline.

This DAG:
1. Extracts and chunks the CV PDF
2. Creates embeddings for each chunk
3. Upserts embeddings into Pinecone
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from app.pdf_loader import process_pdf_to_chunks
from app.embeddings import embed_texts
from app.rag import get_pinecone_client, ensure_pinecone_index
from config.settings import settings


def extract_and_chunk_cv(**context):
    """
    Task 1: Extract text from CV PDF and chunk it.
    Stores chunks in XCom for the next task.
    """
    print(f"Loading PDF from: {settings.cv_pdf_path}")
    chunks = process_pdf_to_chunks()
    print(f"Created {len(chunks)} chunks from PDF")
    
    # Store chunks in XCom
    context['ti'].xcom_push(key='chunks', value=chunks)
    return chunks


def embed_and_upsert_to_pinecone(**context):
    """
    Task 2: Create embeddings and upsert to Pinecone.
    Reads chunks from previous task via XCom.
    """
    # Pull chunks from previous task
    chunks = context['ti'].xcom_pull(key='chunks', task_ids='extract_and_chunk_cv')
    
    if not chunks:
        raise ValueError("No chunks found from previous task")
    
    print(f"Processing {len(chunks)} chunks for embedding...")
    
    # Extract texts for embedding
    texts = [chunk['text'] for chunk in chunks]
    
    # Create embeddings in batches (OpenAI handles batching, but we can be explicit)
    batch_size = 100
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_embeddings = embed_texts(batch_texts)
        all_embeddings.extend(batch_embeddings)
        print(f"Embedded batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")
    
    # Ensure Pinecone index exists
    ensure_pinecone_index()
    
    # Prepare vectors for Pinecone
    vectors = []
    for chunk, embedding in zip(chunks, all_embeddings):
        vectors.append({
            'id': chunk['id'],
            'values': embedding,
            'metadata': chunk['metadata']
        })
    
    # Upsert to Pinecone in batches
    pc = get_pinecone_client()
    index = pc.Index(settings.pinecone_index_name)
    
    upsert_batch_size = 100
    for i in range(0, len(vectors), upsert_batch_size):
        batch_vectors = vectors[i:i + upsert_batch_size]
        index.upsert(vectors=batch_vectors)
        print(f"Upserted batch {i // upsert_batch_size + 1}/{(len(vectors) + upsert_batch_size - 1) // upsert_batch_size}")
    
    print(f"Successfully upserted {len(vectors)} vectors to Pinecone index: {settings.pinecone_index_name}")
    return len(vectors)


# Define DAG
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'cv_ingestion_pipeline',
    default_args=default_args,
    description='Ingest CV PDF, create embeddings, and store in Pinecone',
    schedule_interval='@daily',  # Run daily, or use None for manual triggers only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['rag', 'cv', 'embeddings', 'pinecone'],
)

# Task 1: Extract and chunk CV
extract_task = PythonOperator(
    task_id='extract_and_chunk_cv',
    python_callable=extract_and_chunk_cv,
    dag=dag,
)

# Task 2: Embed and upsert to Pinecone
embed_task = PythonOperator(
    task_id='embed_and_upsert_to_pinecone',
    python_callable=embed_and_upsert_to_pinecone,
    dag=dag,
)

# Set task dependencies
extract_task >> embed_task

