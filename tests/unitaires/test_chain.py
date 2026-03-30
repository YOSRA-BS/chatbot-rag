# =============================================================================
# test_chain.py — Unit tests for RAG chain construction
#
# Tests verify chain building, component integration, and configuration
# of the conversational retrieval chain.
# =============================================================================

import pytest
from unittest.mock import patch, Mock, MagicMock

from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from chain import build_chain


class TestChainBuilding:
    """Test RAG chain construction and configuration."""

    @patch('chain.load_vectorstore')
    @patch('chain.get_retriever')
    @patch('chain.ChatOllama')
    @patch('chain.ConversationalRetrievalChain.from_llm')
    def test_build_chain_creates_conversational_chain(self, mock_from_llm, mock_chat_ollama,
                                                      mock_get_retriever, mock_load_vs):
        """Test that build_chain creates a ConversationalRetrievalChain."""
        # Setup mocks
        mock_vectorstore = Mock()
        mock_load_vs.return_value = mock_vectorstore

        mock_retriever = Mock()
        mock_get_retriever.return_value = mock_retriever

        mock_llm = Mock()
        mock_chat_ollama.return_value = mock_llm

        mock_chain = Mock(spec=ConversationalRetrievalChain)
        mock_from_llm.return_value = mock_chain

        # Execute
        result = build_chain()

        # Verify chain creation
        mock_from_llm.assert_called_once()
        call_kwargs = mock_from_llm.call_args[1]

        assert call_kwargs['llm'] == mock_llm
        assert call_kwargs['retriever'] == mock_retriever
        assert call_kwargs['memory'] is not None
        assert call_kwargs['combine_docs_chain_kwargs'] is not None
        assert call_kwargs['return_source_documents'] is True
        assert call_kwargs['verbose'] is False

        assert result == mock_chain

    @patch('chain.load_vectorstore')
    @patch('chain.get_retriever')
    @patch('chain.ChatOllama')
    @patch('chain.ConversationalRetrievalChain.from_llm')
    def test_build_chain_configures_llm_correctly(self, mock_from_llm, mock_chat_ollama,
                                                  mock_get_retriever, mock_load_vs):
        """Test LLM is configured with correct parameters."""
        from config import OLLAMA_MODEL, OLLAMA_TEMPERATURE

        mock_load_vs.return_value = Mock()
        mock_get_retriever.return_value = Mock()
        mock_from_llm.return_value = Mock()

        build_chain()

        # Verify LLM creation
        mock_chat_ollama.assert_called_once_with(
            model=OLLAMA_MODEL,
            temperature=OLLAMA_TEMPERATURE,
            keep_alive="5m"
        )

    @patch('chain.load_vectorstore')
    @patch('chain.get_retriever')
    @patch('chain.ChatOllama')
    @patch('chain.ConversationalRetrievalChain.from_llm')
    def test_build_chain_configures_retriever_correctly(self, mock_from_llm, mock_chat_ollama,
                                                        mock_get_retriever, mock_load_vs):
        """Test retriever is configured with correct TOP_K."""
        from config import TOP_K

        mock_vectorstore = Mock()
        mock_load_vs.return_value = mock_vectorstore

        mock_retriever = Mock()
        mock_get_retriever.return_value = mock_retriever

        mock_from_llm.return_value = Mock()

        build_chain()

        # Verify retriever creation
        mock_get_retriever.assert_called_once_with(mock_vectorstore, k=TOP_K)

    @patch('chain.load_vectorstore')
    @patch('chain.get_retriever')
    @patch('chain.ChatOllama')
    @patch('chain.ConversationalRetrievalChain.from_llm')
    def test_build_chain_configures_memory(self, mock_from_llm, mock_chat_ollama,
                                           mock_get_retriever, mock_load_vs):
        """Test conversation memory is properly configured."""
        mock_load_vs.return_value = Mock()
        mock_get_retriever.return_value = Mock()
        mock_chat_ollama.return_value = Mock()
        mock_from_llm.return_value = Mock()

        build_chain()

        # Get the memory object passed to from_llm
        call_kwargs = mock_from_llm.call_args[1]
        memory = call_kwargs['memory']

        assert isinstance(memory, ConversationBufferMemory)
        assert memory.memory_key == "chat_history"
        assert memory.return_messages is True
        assert memory.output_key == "answer"

    @patch('chain.load_vectorstore')
    @patch('chain.get_retriever')
    @patch('chain.ChatOllama')
    @patch('chain.ConversationalRetrievalChain.from_llm')
    def test_build_chain_configures_prompt(self, mock_from_llm, mock_chat_ollama,
                                           mock_get_retriever, mock_load_vs):
        """Test prompt template is properly configured."""
        from config import SYSTEM_PROMPT

        mock_load_vs.return_value = Mock()
        mock_get_retriever.return_value = Mock()
        mock_chat_ollama.return_value = Mock()
        mock_from_llm.return_value = Mock()

        build_chain()

        # Get the combine_docs_chain_kwargs
        call_kwargs = mock_from_llm.call_args[1]
        combine_kwargs = call_kwargs['combine_docs_chain_kwargs']
        prompt = combine_kwargs['prompt']

        assert isinstance(prompt, PromptTemplate)
        assert prompt.template == SYSTEM_PROMPT
        assert "context" in prompt.input_variables
        assert "chat_history" in prompt.input_variables
        assert "question" in prompt.input_variables

    @patch('chain.load_vectorstore')
    @patch('chain.get_retriever')
    @patch('chain.ChatOllama')
    @patch('chain.ConversationalRetrievalChain.from_llm')
    def test_build_chain_returns_source_documents(self, mock_from_llm, mock_chat_ollama,
                                                 mock_get_retriever, mock_load_vs):
        """Test chain is configured to return source documents."""
        mock_load_vs.return_value = Mock()
        mock_get_retriever.return_value = Mock()
        mock_chat_ollama.return_value = Mock()
        mock_from_llm.return_value = Mock()

        build_chain()

        call_kwargs = mock_from_llm.call_args[1]
        assert call_kwargs['return_source_documents'] is True

    @patch('chain.load_vectorstore')
    @patch('chain.get_retriever')
    @patch('chain.ChatOllama')
    @patch('chain.ConversationalRetrievalChain.from_llm')
    def test_build_chain_not_verbose(self, mock_from_llm, mock_chat_ollama,
                                    mock_get_retriever, mock_load_vs):
        """Test chain is configured to not be verbose."""
        mock_load_vs.return_value = Mock()
        mock_get_retriever.return_value = Mock()
        mock_chat_ollama.return_value = Mock()
        mock_from_llm.return_value = Mock()

        build_chain()

        call_kwargs = mock_from_llm.call_args[1]
        assert call_kwargs['verbose'] is False


class TestChainIntegration:
    """Test chain integration with mocked components."""

    @patch('chain.load_vectorstore')
    @patch('chain.get_retriever')
    @patch('chain.ChatOllama')
    @patch('chain.ConversationalRetrievalChain.from_llm')
    def test_build_chain_handles_missing_vectorstore(self, mock_from_llm, mock_chat_ollama,
                                                     mock_get_retriever, mock_load_vs):
        """Test chain building fails gracefully when vectorstore is missing."""
        mock_load_vs.side_effect = FileNotFoundError("No vector store found")

        with pytest.raises(FileNotFoundError):
            build_chain()

    @patch('chain.load_vectorstore')
    @patch('chain.get_retriever')
    @patch('chain.ChatOllama')
    @patch('chain.ConversationalRetrievalChain.from_llm')
    def test_build_chain_components_integrate(self, mock_from_llm, mock_chat_ollama,
                                             mock_get_retriever, mock_load_vs):
        """Test all components are properly wired together."""
        # Setup mocks
        mock_vectorstore = Mock()
        mock_load_vs.return_value = mock_vectorstore

        mock_retriever = Mock()
        mock_get_retriever.return_value = mock_retriever

        mock_llm = Mock()
        mock_chat_ollama.return_value = mock_llm

        mock_memory = Mock()
        mock_prompt = Mock()

        # Mock the chain creation to capture what gets passed
        def capture_chain_args(*args, **kwargs):
            # Verify the arguments passed to from_llm
            assert kwargs['llm'] == mock_llm
            assert kwargs['retriever'] == mock_retriever
            assert isinstance(kwargs['memory'], ConversationBufferMemory)
            assert 'prompt' in kwargs['combine_docs_chain_kwargs']
            assert kwargs['return_source_documents'] is True
            assert kwargs['verbose'] is False
            return Mock()

        mock_from_llm.side_effect = capture_chain_args

        # Execute
        chain = build_chain()

        # Verify all mocks were called
        mock_load_vs.assert_called_once()
        mock_get_retriever.assert_called_once()
        mock_chat_ollama.assert_called_once()
        mock_from_llm.assert_called_once()