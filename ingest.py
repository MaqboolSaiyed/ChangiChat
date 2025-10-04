"""Ingest scraped JSONL, create embeddings, and store in local FAISS index.

Run:
    python ingest.py --data scraped_data.jsonl --out faiss_index
"""
import os
import json
import argparse
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

import os
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

def get_embeddings():
    """Get HuggingFace embeddings - more reliable and doesn't require API keys."""
    try:
        # Use a lightweight, reliable embedding model
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},  # Use CPU to avoid GPU requirements
            encode_kwargs={'normalize_embeddings': True}
        )
        print("Successfully initialized HuggingFace embeddings")
        return embeddings
    except Exception as e:
        print(f"Error initializing HuggingFace embeddings: {e}")
        raise


def load_jsonl(path: Path):
    """Load records from a JSONL file and convert them to LangChain `Document`s."""
    docs = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            text = obj.get("text", "").strip()
            if not text:
                continue
            source = obj.get("url", "")
            docs.append(Document(page_content=text, metadata={"source": source}))
    return docs


def build_faiss_index(documents, out_dir: Path):
    print(f"Splitting {len(documents)} documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        add_start_index=True,
        separators=["\n\n", "\n", " ", ""]  # Better handling of markdown and code
    )
    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks from {len(documents)} documents")
    
    # Initialize Google Palm embeddings
    print("Initializing Google Palm embeddings...")
    try:
        embedder = get_embeddings()
        # Test the embedding
        test_embedding = embedder.embed_query("test")
        print(f"Embedding model initialized. Vector dimensions: {len(test_embedding)}")
    except Exception as e:
        print(f"Error initializing embedding model: {e}")
        raise
    
    print("Creating FAISS index...")
    try:
        vectordb = FAISS.from_documents(chunks, embedder)
        print(f"FAISS index created with {vectordb.index.ntotal} vectors")
        
        # Save the index
        vectordb.save_local(str(out_dir))
        print(f"FAISS index saved to {out_dir}")
        
        # Print index info
        print("\n=== FAISS Index Information ===")
        print(f"Number of vectors: {vectordb.index.ntotal}")
        print(f"Vector dimensions: {vectordb.index.d}")
        print("=" * 30 + "\n")
        
    except Exception as e:
        print(f"Error creating FAISS index: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create FAISS vector index from scraped data.")
    parser.add_argument("--data", default="scraped_data.jsonl", help="Path to JSONL file with scraped data.")
    parser.add_argument("--out", default="faiss_index", help="Directory to store FAISS index.")
    args = parser.parse_args()

    data_path = Path(args.data)
    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)

    documents = load_jsonl(data_path)
    if not documents:
        raise ValueError("No valid documents found in the supplied JSONL file.")

    print(f"Loaded {len(documents)} raw documents. Splitting and embedding…")
    build_faiss_index(documents, out_path)
    print(f"FAISS index saved to {out_path.absolute()}")
