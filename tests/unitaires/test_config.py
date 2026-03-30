# =============================================================================
# test_config.py — Unit tests for configuration management
#
# Tests verify that configuration values are properly defined and valid.
# =============================================================================

import pytest
from config import (
    DOCS_FOLDER,
    VECTORSTORE_PATH,
    EMBEDDING_MODEL,
    OLLAMA_MODEL,
    OLLAMA_TEMPERATURE,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K,
    SYSTEM_PROMPT
)


class TestConfigConstants:
    """Test configuration constants are properly defined."""

    def test_paths_are_strings(self):
        """Verify path constants are strings."""
        assert isinstance(DOCS_FOLDER, str)
        assert isinstance(VECTORSTORE_PATH, str)
        assert len(DOCS_FOLDER) > 0
        assert len(VECTORSTORE_PATH) > 0

    def test_embedding_model_defined(self):
        """Verify embedding model is specified."""
        assert isinstance(EMBEDDING_MODEL, str)
        assert len(EMBEDDING_MODEL) > 0
        # Should contain model name
        assert "sentence-transformers" in EMBEDDING_MODEL or "all-MiniLM" in EMBEDDING_MODEL

    def test_ollama_model_defined(self):
        """Verify Ollama model is specified."""
        assert isinstance(OLLAMA_MODEL, str)
        assert len(OLLAMA_MODEL) > 0

    def test_temperature_valid_range(self):
        """Verify temperature is in valid range [0.0, 1.0]."""
        assert isinstance(OLLAMA_TEMPERATURE, (int, float))
        assert 0.0 <= OLLAMA_TEMPERATURE <= 1.0

    def test_chunk_parameters_valid(self):
        """Verify chunk size and overlap are positive integers."""
        assert isinstance(CHUNK_SIZE, int)
        assert isinstance(CHUNK_OVERLAP, int)
        assert CHUNK_SIZE > 0
        assert CHUNK_OVERLAP >= 0
        assert CHUNK_OVERLAP < CHUNK_SIZE  # Overlap should be less than chunk size

    def test_top_k_valid(self):
        """Verify TOP_K is a positive integer."""
        assert isinstance(TOP_K, int)
        assert TOP_K > 0

    def test_system_prompt_structure(self):
        """Verify system prompt has required components."""
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 0
        # Should contain key placeholders
        assert "{context}" in SYSTEM_PROMPT
        assert "{chat_history}" in SYSTEM_PROMPT
        assert "{question}" in SYSTEM_PROMPT
        # Should contain instructions
        assert "context documents" in SYSTEM_PROMPT.lower()
        assert "answer" in SYSTEM_PROMPT.lower()


class TestConfigIntegration:
    """Test configuration values work together."""

    def test_chunk_overlap_reasonable(self):
        """Verify chunk overlap is reasonable relative to chunk size."""
        overlap_ratio = CHUNK_OVERLAP / CHUNK_SIZE
        assert overlap_ratio < 0.5  # Overlap should be less than 50% of chunk size

    def test_temperature_suitable_for_rag(self):
        """Verify temperature is suitable for RAG (factual but natural)."""
        # For RAG, temperature should be low to medium
        assert OLLAMA_TEMPERATURE <= 0.7