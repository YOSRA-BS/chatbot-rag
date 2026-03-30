# =============================================================================
# conftest.py — Shared pytest fixtures for the RAG chatbot test suite
#
# Fixtures provide reusable test data and mocked components to ensure
# tests are isolated, fast, and reliable.
# =============================================================================

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


@pytest.fixture
def tmp_dirs():
    """
    Create temporary directories for testing file operations.
    Cleans up automatically after each test.
    """
    temp_base = tempfile.mkdtemp()
    faiss_base = tempfile.mkdtemp()

    yield {
        'temp_base': temp_base,
        'faiss_base': faiss_base
    }

    # Cleanup
    shutil.rmtree(temp_base, ignore_errors=True)
    shutil.rmtree(faiss_base, ignore_errors=True)


@pytest.fixture
def sample_documents():
    """
    Sample documents for testing document processing.
    """
    return [
        Document(
            page_content="This is a test document about artificial intelligence.",
            metadata={"source": "test1.txt", "page": 1}
        ),
        Document(
            page_content="Machine learning is a subset of AI that enables computers to learn without being explicitly programmed.",
            metadata={"source": "test2.txt", "page": 1}
        ),
        Document(
            page_content="Natural language processing allows computers to understand and generate human language.",
            metadata={"source": "test3.txt", "page": 2}
        )
    ]


@pytest.fixture
def mock_embedding_model():
    """
    Mock embedding model to avoid downloading real models during tests.
    """
    mock_model = Mock(spec=HuggingFaceEmbeddings)
    mock_model.embed_query.return_value = [0.1] * 384  # Mock 384-dim vector
    mock_model.embed_documents.return_value = [[0.1] * 384] * 3
    return mock_model


@pytest.fixture
def mock_vectorstore(sample_documents, mock_embedding_model):
    """
    Mock FAISS vectorstore for testing retrieval components.
    """
    mock_vs = Mock(spec=FAISS)
    mock_vs.similarity_search.return_value = sample_documents[:2]
    mock_vs.as_retriever.return_value = Mock()
    mock_vs.save_local = Mock()
    return mock_vs


@pytest.fixture
def mock_llm():
    """
    Mock LLM for testing chain components without requiring Ollama.
    """
    mock_llm = Mock()
    mock_llm.invoke.return_value = Mock(content="This is a mock response from the LLM.")
    return mock_llm


@pytest.fixture
def stub_model_loader():
    """
    Stub for model loading components in tests.
    """
    return Mock()


@pytest.fixture
def test_config():
    """
    Test configuration values that override production config.
    """
    return {
        'OLLAMA_MODEL': 'test-model',
        'EMBEDDING_MODEL': 'test-embedding',
        'CHUNK_SIZE': 100,
        'CHUNK_OVERLAP': 20,
        'TOP_K': 2,
        'VECTORSTORE_PATH': 'test_vectorstore'
    }