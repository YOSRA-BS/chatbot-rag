# =============================================================================
# test_full_pipeline.py — Integration tests for the complete RAG pipeline
#
# Tests verify end-to-end functionality from document ingestion through
# question answering, ensuring all components work together correctly.
# =============================================================================

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

from langchain_core.documents import Document


class TestFullPipeline:
    """Test the complete RAG pipeline from ingestion to querying."""

    @patch('chain.load_vectorstore')
    @patch('chain.get_retriever')
    @patch('chain.ChatOllama')
    @patch('chain.ConversationalRetrievalChain.from_llm')
    def test_pipeline_initialization(self, mock_from_llm, mock_chat_ollama,
                                    mock_get_retriever, mock_load_vs):
        """Test that the full pipeline can be initialized."""
        from chain import build_chain

        # Setup mocks
        mock_vectorstore = Mock()
        mock_load_vs.return_value = mock_vectorstore

        mock_retriever = Mock()
        mock_get_retriever.return_value = mock_retriever

        mock_llm = Mock()
        mock_chat_ollama.return_value = mock_llm

        mock_chain = Mock()
        mock_chain.invoke.return_value = {
            "answer": "Test answer",
            "source_documents": []
        }
        mock_from_llm.return_value = mock_chain

        # Test chain building
        chain = build_chain()
        assert chain is not None

        # Test query execution
        result = chain.invoke({"question": "What is AI?"})
        assert "answer" in result
        assert "source_documents" in result

    @patch('embeddings.FAISS.from_documents')
    @patch('embeddings.get_embedding_model')
    def test_ingestion_to_vectorstore_pipeline(self, mock_get_model, mock_from_docs):
        """Test the ingestion pipeline creates a proper vectorstore."""
        from embeddings import build_vectorstore

        # Setup mocks
        mock_model = Mock()
        mock_get_model.return_value = mock_model

        mock_vectorstore = Mock()
        mock_from_docs.return_value = mock_vectorstore

        # Test data
        sample_docs = [
            Document(page_content="AI is artificial intelligence.", metadata={"source": "test.txt"}),
            Document(page_content="Machine learning is a subset of AI.", metadata={"source": "test.txt"})
        ]

        # Execute pipeline
        result = build_vectorstore(sample_docs)

        # Verify vectorstore creation
        mock_from_docs.assert_called_once_with(
            documents=sample_docs,
            embedding=mock_model
        )
        mock_vectorstore.save_local.assert_called_once()
        assert result == mock_vectorstore

    def test_document_processing_pipeline(self, sample_documents):
        """Test complete document processing from loading to chunking."""
        from embeddings import split_documents

        # Test document splitting
        chunks = split_documents(sample_documents)

        # Verify chunks are created
        assert len(chunks) > 0
        assert all(isinstance(chunk, Document) for chunk in chunks)

        # Verify metadata preservation
        sources = set(chunk.metadata.get('source') for chunk in chunks)
        original_sources = set(doc.metadata.get('source') for doc in sample_documents)
        assert sources == original_sources

    @patch('chain.load_vectorstore')
    @patch('chain.get_retriever')
    @patch('chain.ChatOllama')
    @patch('chain.ConversationalRetrievalChain.from_llm')
    def test_query_with_sources(self, mock_from_llm, mock_chat_ollama,
                               mock_get_retriever, mock_load_vs, sample_documents):
        """Test querying returns answer with source documents."""
        from chain import build_chain

        # Setup mocks
        mock_vectorstore = Mock()
        mock_load_vs.return_value = mock_vectorstore

        mock_retriever = Mock()
        mock_get_retriever.return_value = mock_retriever

        mock_llm = Mock()
        mock_chat_ollama.return_value = mock_llm

        mock_chain = Mock()
        mock_chain.invoke.return_value = {
            "answer": "AI stands for Artificial Intelligence.",
            "source_documents": sample_documents[:2]
        }
        mock_from_llm.return_value = mock_chain

        # Build and test chain
        chain = build_chain()
        result = chain.invoke({"question": "What is AI?"})

        # Verify response structure
        assert result["answer"] == "AI stands for Artificial Intelligence."
        assert len(result["source_documents"]) == 2
        assert all(isinstance(doc, Document) for doc in result["source_documents"])

    @patch('chain.load_vectorstore')
    @patch('chain.get_retriever')
    @patch('chain.ChatOllama')
    @patch('chain.ConversationalRetrievalChain.from_llm')
    def test_conversation_memory_persistence(self, mock_from_llm, mock_chat_ollama,
                                           mock_get_retriever, mock_load_vs):
        """Test that conversation memory persists across queries."""
        from chain import build_chain

        # Setup mocks
        mock_vectorstore = Mock()
        mock_load_vs.return_value = mock_vectorstore

        mock_retriever = Mock()
        mock_get_retriever.return_value = mock_retriever

        mock_llm = Mock()
        mock_chat_ollama.return_value = mock_llm

        mock_chain = Mock()
        # Mock chain to simulate memory by checking chat_history
        def mock_invoke(input_data):
            chat_history = input_data.get("chat_history", [])
            question = input_data["question"]

            if "follow-up" in question.lower():
                # Should have previous context
                assert len(chat_history) > 0

            return {
                "answer": f"Answer to: {question}",
                "source_documents": [],
                "chat_history": chat_history + [("human", question), ("ai", f"Answer to: {question}")]
            }

        mock_chain.invoke.side_effect = mock_invoke
        mock_from_llm.return_value = mock_chain

        # Build chain and test conversation
        chain = build_chain()

        # First query
        result1 = chain.invoke({"question": "What is AI?"})
        assert "chat_history" in result1

        # Follow-up query (should have memory)
        result2 = chain.invoke({
            "question": "Tell me more about it",
            "chat_history": result1["chat_history"]
        })
        assert "chat_history" in result2


class TestPipelineErrorHandling:
    """Test error handling in the integrated pipeline."""

    @patch('chain.load_vectorstore')
    def test_pipeline_fails_without_vectorstore(self, mock_load_vs):
        """Test pipeline fails gracefully when vectorstore is missing."""
        from chain import build_chain

        mock_load_vs.side_effect = FileNotFoundError("No vector store found")

        with pytest.raises(FileNotFoundError, match="No vector store found"):
            build_chain()

    @patch('embeddings.FAISS.from_documents')
    @patch('embeddings.get_embedding_model')
    def test_ingestion_handles_embedding_errors(self, mock_get_model, mock_from_docs):
        """Test ingestion handles embedding model errors."""
        from embeddings import build_vectorstore

        mock_get_model.side_effect = Exception("Embedding model failed")

        sample_docs = [Document(page_content="test")]

        with pytest.raises(Exception, match="Embedding model failed"):
            build_vectorstore(sample_docs)

    @patch('chain.load_vectorstore')
    @patch('chain.get_retriever')
    @patch('chain.ChatOllama')
    @patch('chain.ConversationalRetrievalChain.from_llm')
    def test_query_handles_llm_errors(self, mock_from_llm, mock_chat_ollama,
                                     mock_get_retriever, mock_load_vs):
        """Test query handling when LLM fails."""
        from chain import build_chain

        # Setup mocks
        mock_vectorstore = Mock()
        mock_load_vs.return_value = mock_vectorstore

        mock_retriever = Mock()
        mock_get_retriever.return_value = mock_retriever

        mock_llm = Mock()
        mock_chat_ollama.return_value = mock_llm

        mock_chain = Mock()
        mock_chain.invoke.side_effect = Exception("LLM failed")
        mock_from_llm.return_value = mock_chain

        chain = build_chain()

        with pytest.raises(Exception, match="LLM failed"):
            chain.invoke({"question": "Test question"})


class TestPipelineConfiguration:
    """Test pipeline configuration and parameter handling."""

    def test_chunk_size_configuration(self, sample_documents):
        """Test that chunk size configuration affects splitting."""
        from config import CHUNK_SIZE, CHUNK_OVERLAP
        from embeddings import split_documents

        # Split with current config
        chunks = split_documents(sample_documents)

        # Verify chunks respect size limits
        for chunk in chunks:
            assert len(chunk.page_content) <= CHUNK_SIZE

    def test_top_k_configuration(self):
        """Test that TOP_K configuration is used in retriever."""
        from config import TOP_K
        from unittest.mock import patch

        with patch('chain.load_vectorstore') as mock_load, \
             patch('chain.get_retriever') as mock_get_retriever, \
             patch('chain.ChatOllama') as mock_ollama, \
             patch('chain.ConversationalRetrievalChain.from_llm') as mock_from_llm:

            mock_vectorstore = Mock()
            mock_load.return_value = mock_vectorstore

            mock_retriever = Mock()
            mock_get_retriever.return_value = mock_retriever

            mock_from_llm.return_value = Mock()

            from chain import build_chain
            build_chain()

            # Verify retriever created with TOP_K
            mock_get_retriever.assert_called_once_with(mock_vectorstore, k=TOP_K)

    def test_temperature_configuration(self):
        """Test that temperature configuration is applied to LLM."""
        from config import OLLAMA_MODEL, OLLAMA_TEMPERATURE
        from unittest.mock import patch

        with patch('chain.load_vectorstore') as mock_load, \
             patch('chain.get_retriever') as mock_get_retriever, \
             patch('chain.ChatOllama') as mock_ollama, \
             patch('chain.ConversationalRetrievalChain.from_llm') as mock_from_llm:

            mock_load.return_value = Mock()
            mock_get_retriever.return_value = Mock()
            mock_from_llm.return_value = Mock()

            from chain import build_chain
            build_chain()

            # Verify LLM created with correct temperature
            mock_ollama.assert_called_once()
            call_args = mock_ollama.call_args[1]
            assert call_args['temperature'] == OLLAMA_TEMPERATURE
            assert call_args['model'] == OLLAMA_MODEL