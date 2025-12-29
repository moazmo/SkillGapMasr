"""
Skill-Gap Masr - Data Ingestion Module

This module handles loading documents (job descriptions and CVs),
chunking them appropriately, generating embeddings, and storing
them in ChromaDB for later retrieval.

Why ChromaDB? It's open-source, runs locally, and persists to disk.
No cloud costs, no API keys needed for storage.

Why HuggingFace embeddings? The all-MiniLM-L6-v2 model runs locally
on your machine (CPU or GPU), is fast, and produces good quality
embeddings for semantic search.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Load environment variables
load_dotenv()

# Import configuration
import config


def load_documents(directory: Path, doc_type: str) -> List[Document]:
    """
    Load all supported documents from a directory.

    Args:
        directory: Path to the directory containing documents
        doc_type: Type identifier ('job_description' or 'student_cv')
                  Added as metadata for filtering during retrieval

    Returns:
        List of Document objects with content and metadata

    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    documents = []

    # Load text files
    try:
        txt_loader = DirectoryLoader(
            str(directory),
            glob="**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            show_progress=True,
        )
        txt_docs = txt_loader.load()

        # Add document type metadata
        for doc in txt_docs:
            doc.metadata["doc_type"] = doc_type
            doc.metadata["source_name"] = Path(doc.metadata["source"]).name

        documents.extend(txt_docs)
        print(f"  ✓ Loaded {len(txt_docs)} .txt files from {directory.name}/")

    except Exception as e:
        print(f"  ⚠ Warning loading .txt files: {e}")

    # Load PDF files (if any)
    try:
        from langchain_community.document_loaders import PyPDFLoader

        pdf_files = list(directory.glob("**/*.pdf"))
        for pdf_path in pdf_files:
            try:
                pdf_loader = PyPDFLoader(str(pdf_path))
                pdf_docs = pdf_loader.load()

                for doc in pdf_docs:
                    doc.metadata["doc_type"] = doc_type
                    doc.metadata["source_name"] = pdf_path.name

                documents.extend(pdf_docs)

            except Exception as e:
                print(f"  ⚠ Error loading {pdf_path.name}: {e}")

        if pdf_files:
            print(f"  ✓ Loaded {len(pdf_files)} .pdf files from {directory.name}/")

    except ImportError:
        print("  ℹ pypdf not available, skipping PDF files")
    except Exception as e:
        print(f"  ⚠ Warning loading .pdf files: {e}")

    return documents


def chunk_documents(documents: List[Document]) -> List[Document]:
    """
    Split documents into smaller chunks for better retrieval.

    We use RecursiveCharacterTextSplitter because it:
    1. Tries to split on paragraph boundaries first
    2. Falls back to sentences, then words
    3. This keeps job requirements/qualifications together

    Args:
        documents: List of Document objects to chunk

    Returns:
        List of chunked Document objects
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
    )

    chunks = text_splitter.split_documents(documents)
    print(f"  ✓ Created {len(chunks)} chunks from {len(documents)} documents")

    return chunks


def create_embeddings() -> HuggingFaceEmbeddings:
    """
    Initialize the HuggingFace embedding model.

    We use all-MiniLM-L6-v2 because:
    1. It's lightweight and fast
    2. Runs on CPU (GPU if available)
    3. Good quality for semantic similarity
    4. 100% free - no API costs

    Returns:
        HuggingFaceEmbeddings instance
    """
    print("  ⏳ Loading embedding model (this may take a moment first time)...")

    embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cpu"},  # Change to "cuda" if you have GPU
        encode_kwargs={"normalize_embeddings": True},
    )

    print(f"  ✓ Loaded embedding model: {config.EMBEDDING_MODEL_NAME}")
    return embeddings


def create_vector_store(
    chunks: List[Document], embeddings: HuggingFaceEmbeddings
) -> Chroma:
    """
    Create or update the ChromaDB vector store.

    ChromaDB is used because:
    1. Open source and free
    2. Persists to disk (survives restarts)
    3. Good performance for MVP scale

    Args:
        chunks: List of document chunks to embed and store
        embeddings: The embedding model instance

    Returns:
        Chroma vector store instance
    """
    # Ensure persist directory exists
    config.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    print(f"  ⏳ Creating embeddings and storing in ChromaDB...")
    print(f"     (Persist location: {config.CHROMA_PERSIST_DIR})")

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(config.CHROMA_PERSIST_DIR),
        collection_name="skill_gap_masr",
    )

    print(f"  ✓ Stored {len(chunks)} chunks in ChromaDB")
    return vector_store


def run_ingestion() -> Optional[Chroma]:
    """
    Main ingestion pipeline entry point.

    Orchestrates the full flow:
    1. Load job descriptions from data/market_jobs/
    2. Load student CVs from data/student_cvs/
    3. Chunk all documents
    4. Generate embeddings and store in ChromaDB

    Returns:
        Chroma vector store instance, or None if failed
    """
    print("\n" + "=" * 60)
    print("🚀 SKILL-GAP MASR - Data Ingestion Pipeline")
    print("=" * 60 + "\n")

    all_documents = []

    # Step 1: Load Job Descriptions
    print("📋 Step 1: Loading Job Descriptions...")
    try:
        job_docs = load_documents(config.DATA_JOBS_DIR, config.DOC_TYPE_JOB)
        all_documents.extend(job_docs)
    except FileNotFoundError as e:
        print(f"  ❌ Error: {e}")
        print(
            "     Please create the data/market_jobs/ directory with job description files."
        )
        return None

    # Step 2: Load Student CVs
    print("\n📄 Step 2: Loading Student CVs...")
    try:
        cv_docs = load_documents(config.DATA_CVS_DIR, config.DOC_TYPE_CV)
        all_documents.extend(cv_docs)
    except FileNotFoundError as e:
        print(f"  ❌ Error: {e}")
        print("     Please create the data/student_cvs/ directory with CV files.")
        return None

    if not all_documents:
        print("\n❌ No documents found! Please add files to the data directories.")
        return None

    # Step 3: Chunk Documents
    print("\n✂️ Step 3: Chunking Documents...")
    chunks = chunk_documents(all_documents)

    # Step 4: Create Embeddings & Store
    print("\n💾 Step 4: Creating Vector Store...")
    embeddings = create_embeddings()
    vector_store = create_vector_store(chunks, embeddings)

    # Summary
    print("\n" + "=" * 60)
    print("✅ INGESTION COMPLETE")
    print("=" * 60)
    print(
        f"   • Job Descriptions: {len([d for d in all_documents if d.metadata.get('doc_type') == config.DOC_TYPE_JOB])}"
    )
    print(
        f"   • Student CVs: {len([d for d in all_documents if d.metadata.get('doc_type') == config.DOC_TYPE_CV])}"
    )
    print(f"   • Total Chunks: {len(chunks)}")
    print(f"   • Vector Store: {config.CHROMA_PERSIST_DIR}")
    print("\n")

    return vector_store


if __name__ == "__main__":
    # Run ingestion when script is executed directly
    run_ingestion()
