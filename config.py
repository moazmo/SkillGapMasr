"""
Skill-Gap Masr - Centralized Configuration

This module contains all configuration constants for the RAG system.
We centralize paths, model names, and chunking parameters here to 
avoid magic strings scattered throughout the codebase.
"""

import os
from pathlib import Path

# =============================================================================
# BASE PATHS
# =============================================================================
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
DATA_JOBS_DIR = DATA_DIR / "market_jobs"
DATA_CVS_DIR = DATA_DIR / "student_cvs"
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"

# =============================================================================
# CHUNKING CONFIGURATION
# =============================================================================
# Using RecursiveCharacterTextSplitter settings optimized for job descriptions
# Chunk size of 500 ensures full "Requirements" sections are captured
# Overlap of 50 prevents cutting off qualification lists mid-sentence
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# =============================================================================
# EMBEDDING MODEL
# =============================================================================
# Using HuggingFace's all-MiniLM-L6-v2:
# - Free and runs locally
# - Fast inference on CPU/GPU
# - Good performance on semantic similarity tasks
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# =============================================================================
# LLM CONFIGURATION
# =============================================================================
# Using Google Gemini (free tier)
# gemini-1.5-flash is fast and has generous free quota
LLM_MODEL_NAME = "gemini-1.5-flash-latest"
LLM_TEMPERATURE = 0.3  # Lower for more focused, factual gap analysis

# =============================================================================
# RETRIEVAL SETTINGS
# =============================================================================
# Number of relevant chunks to retrieve for context
RETRIEVAL_K = 5

# =============================================================================
# SUPPORTED FILE TYPES
# =============================================================================
SUPPORTED_EXTENSIONS = [".txt", ".pdf"]

# =============================================================================
# DOCUMENT METADATA TYPES
# =============================================================================
DOC_TYPE_JOB = "job_description"
DOC_TYPE_CV = "student_cv"
