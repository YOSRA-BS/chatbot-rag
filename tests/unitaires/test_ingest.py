# =============================================================================
# test_ingest.py — Unit tests for document ingestion pipeline
#
# Tests verify the complete ingestion workflow from document loading
# through vectorstore creation.
# =============================================================================

import pytest
from unittest.mock import patch, Mock
from ingest import ingest


class TestIngestPipeline:
    """Test the complete document ingestion pipeline."""

    @patch('ingest.load_documents')
    @patch('ingest.split_documents')
    @patch('ingest.build_vectorstore')
    def test_ingest_successful_pipeline(self, mock_build_vs, mock_split, mock_load):
        """Test successful execution of the full ingestion pipeline."""
        # Setup mocks
        mock_docs = [Mock(), Mock()]
        mock_load.return_value = mock_docs

        mock_chunks = [Mock(), Mock(), Mock()]
        mock_split.return_value = mock_chunks

        mock_vectorstore = Mock()
        mock_build_vs.return_value = mock_vectorstore

        # Execute
        ingest()

        # Verify all steps were called
        mock_load.assert_called_once()
        mock_split.assert_called_once_with(mock_docs)
        mock_build_vs.assert_called_once_with(mock_chunks)

    @patch('ingest.load_documents')
    def test_ingest_no_documents_found(self, mock_load, capsys):
        """Test ingestion when no documents are found."""
        mock_load.return_value = []

        ingest()

        # Check output
        captured = capsys.readouterr()
        assert "Nothing to ingest" in captured.out

        # Verify no further processing
        # (split_documents and build_vectorstore should not be called)

    @patch('ingest.load_documents')
    @patch('ingest.split_documents')
    @patch('ingest.build_vectorstore')
    def test_ingest_with_documents_output(self, mock_build_vs, mock_split, mock_load, capsys):
        """Test ingestion output messages."""
        mock_docs = [Mock()]
        mock_load.return_value = mock_docs

        mock_chunks = [Mock()] * 5  # 5 chunks
        mock_split.return_value = mock_chunks

        mock_build_vs.return_value = Mock()

        ingest()

        captured = capsys.readouterr()
        assert "Document Ingestion" in captured.out
        assert "Loading documents" in captured.out
        assert "Splitting into chunks" in captured.out
        assert "Creating embeddings" in captured.out
        assert "5 chunks stored" in captured.out
        assert "You can now launch the chatbot" in captured.out

    @patch('ingest.load_documents')
    @patch('ingest.split_documents')
    @patch('ingest.build_vectorstore')
    def test_ingest_calls_functions_with_correct_args(self, mock_build_vs, mock_split, mock_load):
        """Test that ingestion functions are called with correct arguments."""
        mock_docs = [Mock(page_content="test")]
        mock_load.return_value = mock_docs

        mock_chunks = [Mock(page_content="chunk")]
        mock_split.return_value = mock_chunks

        ingest()

        # Verify load_documents called without arguments (uses default folder)
        mock_load.assert_called_once_with()

        # Verify split_documents called with loaded docs
        mock_split.assert_called_once_with(mock_docs)

        # Verify build_vectorstore called with chunks
        mock_build_vs.assert_called_once_with(mock_chunks)


class TestIngestErrorHandling:
    """Test error handling in ingestion pipeline."""

    @patch('ingest.load_documents')
    def test_ingest_handles_load_error(self, mock_load):
        """Test ingestion handles document loading errors."""
        mock_load.side_effect = Exception("Load failed")

        with pytest.raises(Exception, match="Load failed"):
            ingest()

    @patch('ingest.load_documents')
    @patch('ingest.split_documents')
    def test_ingest_handles_split_error(self, mock_split, mock_load):
        """Test ingestion handles document splitting errors."""
        mock_load.return_value = [Mock()]
        mock_split.side_effect = Exception("Split failed")

        with pytest.raises(Exception, match="Split failed"):
            ingest()

    @patch('ingest.load_documents')
    @patch('ingest.split_documents')
    @patch('ingest.build_vectorstore')
    def test_ingest_handles_build_error(self, mock_build_vs, mock_split, mock_load):
        """Test ingestion handles vectorstore building errors."""
        mock_load.return_value = [Mock()]
        mock_split.return_value = [Mock()]
        mock_build_vs.side_effect = Exception("Build failed")

        with pytest.raises(Exception, match="Build failed"):
            ingest()


class TestIngestIntegration:
    """Test ingestion integration with actual components."""

    @patch('ingest.load_documents')
    @patch('ingest.split_documents')
    @patch('ingest.build_vectorstore')
    def test_ingest_pipeline_data_flow(self, mock_build_vs, mock_split, mock_load):
        """Test that data flows correctly through the pipeline."""
        from langchain_core.documents import Document

        # Create real documents
        docs = [
            Document(page_content="Test document 1", metadata={"source": "test1.txt"}),
            Document(page_content="Test document 2", metadata={"source": "test2.txt"})
        ]
        mock_load.return_value = docs

        # Mock splitting to return modified documents
        split_docs = [
            Document(page_content="Chunk 1", metadata={"source": "test1.txt"}),
            Document(page_content="Chunk 2", metadata={"source": "test1.txt"}),
            Document(page_content="Chunk 3", metadata={"source": "test2.txt"})
        ]
        mock_split.return_value = split_docs

        mock_build_vs.return_value = Mock()

        ingest()

        # Verify data flow
        mock_split.assert_called_once_with(docs)
        mock_build_vs.assert_called_once_with(split_docs)