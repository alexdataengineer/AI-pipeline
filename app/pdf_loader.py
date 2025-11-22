"""
PDF loading and text chunking utilities.
"""
import hashlib
from typing import List, Dict
from pypdf import PdfReader
from config.settings import settings


def load_pdf(pdf_path: str = None) -> List[Dict[str, str]]:
    """
    Load PDF and extract text page by page.
    
    Args:
        pdf_path: Path to PDF file. If None, uses settings.cv_pdf_path.
        
    Returns:
        List of dictionaries with 'page_number' and 'text' keys.
    """
    if pdf_path is None:
        pdf_path = settings.cv_pdf_path
    
    reader = PdfReader(pdf_path)
    pages = []
    
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text.strip():  # Only add non-empty pages
            pages.append({
                'page_number': page_num,
                'text': text
            })
    
    return pages


def chunk_text(text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of characters to overlap between chunks.
        
    Returns:
        List of text chunks.
    """
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if chunk_overlap is None:
        chunk_overlap = settings.chunk_overlap
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at word boundary if not at end of text
        if end < len(text):
            # Find last space or newline in the chunk
            last_break = max(
                chunk.rfind(' '),
                chunk.rfind('\n'),
                chunk.rfind('.'),
                chunk.rfind('!'),
                chunk.rfind('?')
            )
            if last_break > chunk_size * 0.5:  # Only break if we're at least halfway
                chunk = chunk[:last_break + 1]
                end = start + last_break + 1
        
        chunks.append(chunk.strip())
        start = end - chunk_overlap
    
    return chunks


def process_pdf_to_chunks(pdf_path: str = None) -> List[Dict[str, any]]:
    """
    Load PDF and convert to chunks with metadata.
    
    Args:
        pdf_path: Path to PDF file. If None, uses settings.cv_pdf_path.
        
    Returns:
        List of chunk dictionaries with:
        - id: Unique chunk ID
        - text: Chunk text
        - page_number: Source page number
        - metadata: Additional metadata dict
    """
    pages = load_pdf(pdf_path)
    all_chunks = []
    
    for page_data in pages:
        page_num = page_data['page_number']
        page_text = page_data['text']
        
        # Chunk the page text
        page_chunks = chunk_text(page_text)
        
        for chunk_idx, chunk_content in enumerate(page_chunks):
            # Generate unique ID: page_number + chunk_index hash
            chunk_id_str = f"page_{page_num}_chunk_{chunk_idx}_{chunk_content[:50]}"
            chunk_id = hashlib.md5(chunk_id_str.encode()).hexdigest()
            
            chunk_data = {
                'id': chunk_id,
                'text': chunk_content,
                'page_number': page_num,
                'chunk_index': chunk_idx,
                'metadata': {
                    'text': chunk_content,
                    'page': page_num,
                    'chunk_index': chunk_idx
                }
            }
            all_chunks.append(chunk_data)
    
    return all_chunks

