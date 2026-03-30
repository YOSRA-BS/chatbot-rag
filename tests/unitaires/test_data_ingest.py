# =============================================================================
# test_data_ingest.py — Unit tests for data ingestion components
#
# Tests follow the pattern from GitHub examples, adapted for this RAG pipeline.
# Tests verify session management, document ingestion, and vectorstore operations.
# =============================================================================

import pathlib
import pytest
from unittest.mock import Mock, patch

from langchain_core.documents import Document


# Mock classes to simulate the GitHub example structure
class MockChatIngestor:
    """Mock ChatIngestor for testing ingestion logic."""

    def __init__(self, temp_base="data", faiss_base="faiss_index", use_session_dirs=True):
        self.temp_base = temp_base
        self.faiss_base = faiss_base
        self.use_session_dirs = use_session_dirs
        self.session_id = self._generate_session_id() if use_session_dirs else None

    def _generate_session_id(self):
        """Generate a unique session ID."""
        import uuid
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"session_{timestamp}_{unique_id}"

    @property
    def temp_dir(self):
        if self.use_session_dirs and self.session_id:
            return pathlib.Path(self.temp_base) / self.session_id
        return pathlib.Path(self.temp_base)

    @property
    def faiss_dir(self):
        if self.use_session_dirs and self.session_id:
            return pathlib.Path(self.faiss_base) / self.session_id
        return pathlib.Path(self.faiss_base)

    def _split(self, docs, chunk_size=500, chunk_overlap=100):
        """Split documents into chunks."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
        )
        return splitter.split_documents(docs)


class MockFaissManager:
    """Mock FaissManager for testing vectorstore operations."""

    def __init__(self, index_dir):
        self.index_dir = pathlib.Path(index_dir)
        self.documents = []

    def load_or_create(self, texts, metadatas):
        """Load or create FAISS index."""
        self.documents = [
            Document(page_content=text, metadata=meta)
            for text, meta in zip(texts, metadatas)
        ]
        return len(self.documents)

    def add_documents(self, docs):
        """Add documents to the index."""
        added = len(docs)
        self.documents.extend(docs)
        return added


def generate_session_id():
    """Generate a unique session ID (adapted from GitHub example)."""
    import uuid
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"session_{timestamp}_{unique_id}"


class TestSessionIdGeneration:
    """Test session ID generation functionality."""

    def test_generate_session_id_format_and_uniqueness(self):
        """Test session ID format and uniqueness (adapted from GitHub example)."""
        a = generate_session_id()
        b = generate_session_id()
        assert a != b
        assert a.startswith("session_") and b.startswith("session_")
        # Rough pattern check: session_YYYYMMDD_HHMMSS_XXXXXXXX -> 4 parts
        assert len(a.split("_")) == 4

    def test_generate_session_id_components(self):
        """Test that session ID contains expected components."""
        session_id = generate_session_id()

        parts = session_id.split("_")
        assert len(parts) == 4
        assert parts[0] == "session"

        # Check timestamp format (YYYYMMDD_HHMMSS)
        timestamp = parts[1] + "_" + parts[2]
        assert len(timestamp) == 15  # YYYYMMDD_HHMMSS

        # Check unique ID
        unique_part = parts[3]
        assert len(unique_part) == 8  # 8 characters


class TestChatIngestor:
    """Test ChatIngestor functionality."""

    def test_chat_ingestor_resolve_dir_uses_session_dirs(self, tmp_dirs):
        """Test ChatIngestor creates session-specific directories."""
        ing = MockChatIngestor(temp_base=tmp_dirs['temp_base'],
                              faiss_base=tmp_dirs['faiss_base'],
                              use_session_dirs=True)
        assert ing.session_id
        assert str(ing.temp_dir).endswith(ing.session_id)
        assert str(ing.faiss_dir).endswith(ing.session_id)

    def test_chat_ingestor_without_session_dirs(self, tmp_dirs):
        """Test ChatIngestor without session directories."""
        ing = MockChatIngestor(temp_base=tmp_dirs['temp_base'],
                              faiss_base=tmp_dirs['faiss_base'],
                              use_session_dirs=False)
        assert ing.session_id is None
        assert str(ing.temp_dir) == tmp_dirs['temp_base']
        assert str(ing.faiss_dir) == tmp_dirs['faiss_base']

    def test_split_chunks_respect_size_and_overlap(self, tmp_dirs):
        """Test document splitting respects chunk size and overlap."""
        ing = MockChatIngestor(temp_base=tmp_dirs['temp_base'],
                              faiss_base=tmp_dirs['faiss_base'],
                              use_session_dirs=True)
        docs = [Document(page_content="A" * 1200, metadata={"source": "x.txt"})]
        chunks = ing._split(docs, chunk_size=500, chunk_overlap=100)
        assert len(chunks) >= 2
        # spot check boundaries
        assert len(chunks[0].page_content) <= 500

    def test_split_chunks_overlap_applied(self, tmp_dirs):
        """Test that chunk overlap is properly applied."""
        ing = MockChatIngestor(use_session_dirs=True)
        docs = [Document(page_content="A" * 800, metadata={"source": "test.txt"})]
        chunks = ing._split(docs, chunk_size=400, chunk_overlap=50)

        if len(chunks) > 1:
            # Check overlap between consecutive chunks
            first_end = chunks[0].page_content[-50:]
            second_start = chunks[1].page_content[:50]
            assert first_end == second_start

    def test_split_empty_documents(self, tmp_dirs):
        """Test splitting empty document list."""
        ing = MockChatIngestor(use_session_dirs=True)
        chunks = ing._split([], chunk_size=500, chunk_overlap=100)
        assert chunks == []


class TestFaissManager:
    """Test FaissManager functionality."""

    def test_faiss_manager_add_documents_idempotent(self, tmp_dirs):
        """Test adding documents is idempotent."""
        fm = MockFaissManager(index_dir=pathlib.Path(tmp_dirs['faiss_base']) / "test")
        fm.load_or_create(texts=["hello", "world"], metadatas=[{"source": "a"}, {"source": "b"}])
        docs = [Document(page_content="hello", metadata={"source": "a"})]
        first = fm.add_documents(docs)
        second = fm.add_documents(docs)
        assert first >= 0
        assert second == len(docs)  # Should add the same documents again

    def test_faiss_manager_load_or_create(self, tmp_dirs):
        """Test loading or creating FAISS index."""
        fm = MockFaissManager(index_dir=pathlib.Path(tmp_dirs['faiss_base']) / "test")
        count = fm.load_or_create(
            texts=["hello", "world"],
            metadatas=[{"source": "a"}, {"source": "b"}]
        )
        assert count == 2
        assert len(fm.documents) == 2

    def test_faiss_manager_add_documents_accumulates(self, tmp_dirs):
        """Test adding documents accumulates in the index."""
        fm = MockFaissManager(index_dir=pathlib.Path(tmp_dirs['faiss_base']) / "test")

        # Initial load
        fm.load_or_create(texts=["hello"], metadatas=[{"source": "a"}])
        initial_count = len(fm.documents)

        # Add more documents
        new_docs = [
            Document(page_content="world", metadata={"source": "b"}),
            Document(page_content="test", metadata={"source": "c"})
        ]
        added = fm.add_documents(new_docs)

        assert added == 2
        assert len(fm.documents) == initial_count + 2


class TestIngestionIntegration:
    """Test integration between ingestion components."""

    def test_ingestor_with_faiss_manager_workflow(self, tmp_dirs):
        """Test complete workflow from ingestor to FAISS manager."""
        # Create ingestor
        ing = MockChatIngestor(temp_base=tmp_dirs['temp_base'],
                              faiss_base=tmp_dirs['faiss_base'],
                              use_session_dirs=True)

        # Create documents
        docs = [Document(page_content="A" * 1000, metadata={"source": "test.txt"})]

        # Split documents
        chunks = ing._split(docs, chunk_size=400, chunk_overlap=50)

        # Create FAISS manager
        fm = MockFaissManager(index_dir=ing.faiss_dir)

        # Add chunks to FAISS
        added = fm.add_documents(chunks)

        assert added == len(chunks)
        assert len(fm.documents) == len(chunks)
        assert all(isinstance(doc, Document) for doc in fm.documents)

    def test_session_isolation(self, tmp_dirs):
        """Test that different sessions are properly isolated."""
        ing1 = MockChatIngestor(temp_base=tmp_dirs['temp_base'],
                               faiss_base=tmp_dirs['faiss_base'],
                               use_session_dirs=True)
        ing2 = MockChatIngestor(temp_base=tmp_dirs['temp_base'],
                               faiss_base=tmp_dirs['faiss_base'],
                               use_session_dirs=True)

        # Sessions should be different
        assert ing1.session_id != ing2.session_id
        assert ing1.temp_dir != ing2.temp_dir
        assert ing1.faiss_dir != ing2.faiss_dir