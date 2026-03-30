# =============================================================================
# test_embeddings.py — Unit tests for embedding and vectorstore functionality
#
# Tests verify text splitting, embedding creation, FAISS operations, and
# vectorstore persistence/loading.
# =============================================================================

from config import EMBEDDING_MODEL
import pytest
import tempfile
import shutil# Add retry logic for file deletion on Windows
import time
def safe_unlink(path):
    for _ in range(3):
        try:
            path.unlink()
            break
        except PermissionError:
            time.sleep(0.1)
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import time

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from embeddings import (
    get_embedding_model,
    split_documents,
    build_vectorstore,
    load_vectorstore,
    get_retriever
)


class TestEmbeddingModel:
    """Test embedding model initialization and configuration."""

    @patch('embeddings.HuggingFaceEmbeddings')
    def test_get_embedding_model_creates_instance(self, mock_embeddings):
        """Test embedding model is created with correct parameters."""
        mock_model = Mock()
        mock_embeddings.return_value = mock_model

        model = get_embedding_model()

        mock_embeddings.assert_called_once()
        call_kwargs = mock_embeddings.call_args[1]
        assert call_kwargs['model_kwargs']['device'] == 'cpu'
        assert call_kwargs['encode_kwargs']['normalize_embeddings'] is True

    @patch('embeddings.HuggingFaceEmbeddings')
    def test_get_embedding_model_uses_config_model(self, mock_embeddings):
        """Test embedding model uses configured model name."""
        from config import EMBEDDING_MODEL

        mock_model = Mock()
        mock_embeddings.return_value = mock_model

        model = get_embedding_model()

        # Verify the model was called with the correct model_name
        mock_embeddings.assert_called_once()
        call_kwargs = mock_embeddings.call_args[1]
        assert call_kwargs['model_name'] == EMBEDDING_MODEL


class TestDocumentSplitting:
    """Test document splitting into chunks."""

    def test_split_documents_basic(self, sample_documents):
        """Test basic document splitting."""
        chunks = split_documents(sample_documents)

        assert len(chunks) >= len(sample_documents)  # May create multiple chunks
        for chunk in chunks:
            assert isinstance(chunk, Document)
            assert 'page_content' in chunk.__dict__
            assert 'metadata' in chunk.__dict__

    def test_split_documents_preserves_metadata(self, sample_documents):
        """Test that metadata is preserved during splitting."""
        chunks = split_documents(sample_documents)

        # Find chunks from first document
        source_chunks = [c for c in chunks if c.metadata.get('source') == 'test1.txt']
        assert len(source_chunks) > 0

        for chunk in source_chunks:
            assert chunk.metadata['source'] == 'test1.txt'
            assert 'page' in chunk.metadata

    def test_split_large_document_creates_multiple_chunks(self):
        """Test that large documents are split into multiple chunks."""
        large_content = "This is a test sentence. " * 100  # Long content
        large_doc = Document(
            page_content=large_content,
            metadata={"source": "large.txt"}
        )

        chunks = split_documents([large_doc])

        assert len(chunks) > 1  # Should be split into multiple chunks
        total_content = ''.join(c.page_content for c in chunks)
        assert len(total_content) >= len(large_content)  # Overlap may add content

    def test_split_empty_documents(self):
        """Test splitting empty document list."""
        chunks = split_documents([])
        assert chunks == []

    def test_split_documents_chunk_size_respected(self):
        """Test that chunk size limits are respected."""
        from config import CHUNK_SIZE

        # Create document larger than chunk size
        long_content = "A" * (CHUNK_SIZE + 100)
        doc = Document(page_content=long_content, metadata={"source": "long.txt"})

        chunks = split_documents([doc])

        for chunk in chunks:
            assert len(chunk.page_content) <= CHUNK_SIZE

    def test_split_documents_overlap_applied(self):
        """Test that chunk overlap is applied correctly."""
        from config import CHUNK_OVERLAP

        # Create content that will definitely split
        content = "Word " * 200  # Long content
        doc = Document(page_content=content, metadata={"source": "overlap.txt"})

        chunks = split_documents([doc])

        if len(chunks) > 1:
            # Check that there's some overlap (not exact string match)
            overlap_found = any(
                chunk.page_content[:CHUNK_OVERLAP] in chunks[0].page_content[-CHUNK_OVERLAP*2:] 
                for chunk in chunks[1:]
            )
            assert overlap_found, "Expected some overlap between chunks"


class TestVectorstoreBuilding:
    """Test FAISS vectorstore creation and persistence."""

    @patch('embeddings.FAISS.from_documents')
    @patch('embeddings.get_embedding_model')
    def test_build_vectorstore_creates_faiss_index(self, mock_get_model, mock_from_docs, tmp_dirs):
        """Test vectorstore building creates FAISS index."""
        mock_model = Mock()
        mock_get_model.return_value = mock_model

        mock_vectorstore = Mock()
        mock_from_docs.return_value = mock_vectorstore

        sample_docs = [Document(page_content="test", metadata={"source": "test.txt"})]
        result = build_vectorstore(sample_docs)

        mock_from_docs.assert_called_once_with(
            documents=sample_docs,
            embedding=mock_model
        )
        mock_vectorstore.save_local.assert_called_once()
        assert result == mock_vectorstore

    @patch('embeddings.get_embedding_model')
    @patch('embeddings.FAISS.from_documents')
    def test_build_vectorstore_saves_to_correct_path(self, mock_from_docs, mock_get_model, tmp_dirs):
        """Test vectorstore is saved to configured path."""
        from config import VECTORSTORE_PATH

        mock_vectorstore = Mock()
        mock_from_docs.return_value = mock_vectorstore

        sample_docs = [Document(page_content="test")]
        build_vectorstore(sample_docs)

        mock_vectorstore.save_local.assert_called_once_with(VECTORSTORE_PATH)

    def test_build_vectorstore_creates_directory(self, tmp_dirs):
        """Test vectorstore creation creates necessary directories."""
        from config import VECTORSTORE_PATH

        # Ensure directory doesn't exist
        vs_path = Path(VECTORSTORE_PATH)
        if vs_path.exists():
            shutil.rmtree(vs_path)

        with patch('embeddings.FAISS.from_documents') as mock_from_docs:
            mock_vectorstore = Mock()
            mock_from_docs.return_value = mock_vectorstore

            sample_docs = [Document(page_content="test")]
            build_vectorstore(sample_docs)

            # Directory should be created
            assert vs_path.exists()
            assert vs_path.is_dir()


class TestVectorstoreLoading:
    """Test FAISS vectorstore loading from disk."""

    def test_load_vectorstore_missing_index_raises_error(self):
        """Test loading non-existent vectorstore raises FileNotFoundError."""
        from config import VECTORSTORE_PATH

        # Ensure no index exists
        index_path = Path(VECTORSTORE_PATH) / "index.faiss"
        if index_path.exists():
            index_path.unlink()

        with pytest.raises(FileNotFoundError, match="No vector store found"):
            load_vectorstore()

    @patch('embeddings.FAISS.load_local')
    @patch('embeddings.get_embedding_model')
    def test_load_vectorstore_success(self, mock_get_model, mock_load_local):
        """Test successful vectorstore loading."""
        from config import VECTORSTORE_PATH

        mock_model = Mock()
        mock_get_model.return_value = mock_model

        mock_vectorstore = Mock()
        mock_load_local.return_value = mock_vectorstore

        # Create the index file so check passes
        vs_path = Path(VECTORSTORE_PATH)
        vs_path.mkdir(exist_ok=True)
        (vs_path / "index.faiss").touch()

        try:
            result = load_vectorstore()

            mock_load_local.assert_called_once_with(
                VECTORSTORE_PATH,
                mock_model,
                allow_dangerous_deserialization=True
            )
            assert result == mock_vectorstore
        finally:
            shutil.rmtree(vs_path, ignore_errors=True)

    @patch('embeddings.FAISS.load_local')
    @patch('embeddings.get_embedding_model')
    def test_load_vectorstore_allows_dangerous_deserialization(self, mock_get_model, mock_load_local):
        """Test that dangerous deserialization is allowed for FAISS loading."""
        from config import VECTORSTORE_PATH

        mock_model = Mock()
        mock_get_model.return_value = mock_model

        mock_vectorstore = Mock()
        mock_load_local.return_value = mock_vectorstore

        # Create the index file
        vs_path = Path(VECTORSTORE_PATH)
        vs_path.mkdir(exist_ok=True)
        (vs_path / "index.faiss").touch()

        try:
            load_vectorstore()

            call_kwargs = mock_load_local.call_args[1]
            assert call_kwargs['allow_dangerous_deserialization'] is True
        finally:
            shutil.rmtree(vs_path, ignore_errors=True)


class TestRetrieverCreation:
    """Test retriever creation from vectorstore."""

    def test_get_retriever_creates_retriever(self, mock_vectorstore):
        """Test retriever is created with correct parameters."""
        k = 5
        retriever = get_retriever(mock_vectorstore, k)

        mock_vectorstore.as_retriever.assert_called_once_with(
            search_type="similarity",
            search_kwargs={"k": k}
        )

    def test_get_retriever_uses_similarity_search(self, mock_vectorstore):
        """Test retriever uses similarity search."""
        retriever = get_retriever(mock_vectorstore, 3)

        call_kwargs = mock_vectorstore.as_retriever.call_args[1]
        assert call_kwargs['search_type'] == 'similarity'
        assert call_kwargs['search_kwargs']['k'] == 3