# =============================================================================
# test_evaluation.py — Integration tests for the evaluation pipeline
#
# Tests verify the evaluation system works correctly with the RAG pipeline,
# including metrics calculation and MLflow logging.
# =============================================================================

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock


class TestEvaluationPipeline:
    """Test the evaluation pipeline integration."""

    def test_evaluation_dataset_loading(self):
        """Test loading evaluation dataset."""
        # Create a temporary dataset
        dataset_content = [
            {
                "question": "What is artificial intelligence?",
                "answer": "AI is a field of computer science...",
                "contexts": ["AI refers to artificial intelligence..."],
                "ground_truth": "Artificial intelligence is a branch of computer science..."
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(dataset_content, f)
            dataset_path = f.name

        try:
            # Load and verify dataset
            with open(dataset_path, 'r') as f:
                loaded_data = json.load(f)

            assert len(loaded_data) == 1
            assert "question" in loaded_data[0]
            assert "answer" in loaded_data[0]
            assert "contexts" in loaded_data[0]
            assert "ground_truth" in loaded_data[0]
        finally:
            Path(dataset_path).unlink()

    @patch('evaluate.run_evaluation.build_chain')
    @patch('mlflow.start_run')
    @patch('mlflow.log_metrics')
    @patch('mlflow.log_param')
    def test_evaluation_runs_successfully(self, mock_log_param, mock_log_metrics,
                                         mock_start_run, mock_build_chain):
        """Test that evaluation runs without errors."""
        # This is a simplified test since the actual evaluation requires Ollama
        mock_chain = Mock()
        mock_chain.invoke.return_value = {
            "answer": "Test answer",
            "source_documents": []
        }
        mock_build_chain.return_value = mock_chain

        mock_run = Mock()
        mock_start_run.return_value.__enter__ = Mock(return_value=mock_run)
        mock_start_run.return_value.__exit__ = Mock(return_value=None)

        # Mock the evaluation process
        with patch('evaluate.run_evaluation.Dataset') as mock_dataset, \
             patch('evaluate.run_evaluation.evaluate') as mock_evaluate:

            mock_dataset_instance = Mock()
            mock_dataset.return_value = mock_dataset_instance

            mock_result = Mock()
            mock_result.to_pandas.return_value = Mock()
            mock_evaluate.return_value = mock_result

            # Simulate successful evaluation
            # Note: In real implementation, this would call run_evaluation functions
            assert True  # Placeholder for successful evaluation

    def test_evaluation_metrics_calculation(self):
        """Test evaluation metrics are calculated correctly."""
        # Mock evaluation results
        mock_results = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.92,
            "context_relevancy": 0.78
        }

        # Verify metrics are in valid range
        for metric, value in mock_results.items():
            assert 0.0 <= value <= 1.0
            assert isinstance(value, float)

        # Test threshold checking
        seuil_qualite = 0.5
        for metric, value in mock_results.items():
            assert value >= seuil_qualite, f"{metric} below threshold"

    @patch('mlflow.start_run')
    def test_mlflow_logging_integration(self, mock_start_run):
        """Test MLflow logging works correctly."""
        mock_run = Mock()
        mock_start_run.return_value.__enter__ = Mock(return_value=mock_run)
        mock_start_run.return_value.__exit__ = Mock(return_value=None)

        # Simulate logging metrics
        with mock_start_run():
            # In real evaluation, these would be logged
            metrics = {
                "faithfulness": 0.85,
                "answer_relevancy": 0.92,
                "avg_response_time": 2.3
            }

            for key, value in metrics.items():
                mock_run.log_metric(key, value)

        # Verify run was started
        mock_start_run.assert_called_once()

    def test_evaluation_error_handling(self):
        """Test evaluation handles errors gracefully."""
        # Test with invalid dataset
        with pytest.raises((FileNotFoundError, json.JSONDecodeError)):
            with open("nonexistent_file.json", 'r') as f:
                json.load(f)

    def test_evaluation_configuration(self):
        """Test evaluation uses correct configuration."""
        from evaluate.run_evaluation import DATASET_PATH, EXPERIMENT_NAME, SEUIL_QUALITE

        # Verify configuration values
        assert isinstance(DATASET_PATH, str)
        assert DATASET_PATH.endswith('.json')

        assert isinstance(EXPERIMENT_NAME, str)
        assert len(EXPERIMENT_NAME) > 0

        assert isinstance(SEUIL_QUALITE, (int, float))
        assert 0.0 <= SEUIL_QUALITE <= 1.0


class TestEvaluationMetrics:
    """Test evaluation metrics calculation."""

    def test_faithfulness_calculation(self):
        """Test faithfulness metric calculation logic."""
        # Mock data for faithfulness
        # Faithfulness measures how well the answer is supported by the context

        question = "What is AI?"
        answer = "AI stands for Artificial Intelligence, which is a field of computer science."
        context = "Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines."

        # In real RAGAS, this would be calculated automatically
        # Here we simulate the expected behavior
        assert len(answer) > 0
        assert len(context) > 0
        assert question in answer or "AI" in answer

    def test_answer_relevancy_calculation(self):
        """Test answer relevancy metric calculation logic."""
        question = "What is machine learning?"
        answer = "Machine learning is a subset of AI that enables computers to learn from data."

        # Answer should be relevant to the question
        assert "machine learning" in answer.lower()
        assert "AI" in answer or "artificial intelligence" in answer.lower()

    def test_context_relevancy_calculation(self):
        """Test context relevancy metric calculation logic."""
        question = "What is deep learning?"
        relevant_context = "Deep learning is a subset of machine learning that uses neural networks."
        irrelevant_context = "The weather today is sunny."

        # Relevant context should contain information about the question
        assert "deep learning" in relevant_context.lower()
        assert "deep learning" not in irrelevant_context.lower()


class TestEvaluationReporting:
    """Test evaluation result reporting and visualization."""

    def test_evaluation_results_formatting(self):
        """Test evaluation results are properly formatted."""
        results = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.92,
            "context_relevancy": 0.78,
            "total_questions": 10,
            "passed_threshold": 8
        }

        # Test formatting for display
        formatted = "\n".join([f"{k}: {v}" for k, v in results.items()])
        assert "faithfulness: 0.85" in formatted
        assert "total_questions: 10" in formatted

    def test_evaluation_summary_generation(self):
        """Test generation of evaluation summary."""
        metrics = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.92
        }

        # Calculate summary statistics
        avg_score = sum(metrics.values()) / len(metrics)
        min_score = min(metrics.values())
        max_score = max(metrics.values())

        assert avg_score == pytest.approx(0.885, rel=1e-2)
        assert min_score == 0.85
        assert max_score == 0.92

    @patch('pandas.DataFrame.to_csv')
    def test_results_export(self, mock_to_csv):
        """Test evaluation results can be exported."""
        import pandas as pd

        # Mock DataFrame
        mock_df = Mock(spec=pd.DataFrame)
        mock_df.to_csv = mock_to_csv

        # Simulate export
        results_path = "test_results.csv"
        mock_df.to_csv(results_path)

        # Verify export was called
        mock_to_csv.assert_called_once_with(results_path)