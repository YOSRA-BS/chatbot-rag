# =============================================================================
# test_loader.py — Unit tests for document loading functionality
#
# Tests verify document loading from various file formats, error handling,
# and proper metadata extraction.
# =============================================================================

import pytest
import tempfile
import shutil
import time
import os
from pathlib import Path
from unittest.mock import patch, Mock

from langchain_core.documents import Document
from loader import load_documents, _load_single_file, SUPPORTED_EXTENSIONS


def safe_unlink(file_path: Path, max_retries: int = 3, delay: float = 0.1):
    """Safely unlink a file with retry logic for Windows file locking issues."""
    for attempt in range(max_retries):
        try:
            file_path.unlink()
            return
        except PermissionError:
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                # On Windows, file handles may be held longer, try force remove
                try:
                    os.remove(str(file_path))
                except OSError:
                    pass  # Ignore if still can't delete


class TestLoadDocuments:
    """Test document loading from directory."""

    def test_load_empty_directory(self):
        """Test loading from empty directory returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = load_documents(tmpdir)
            assert docs == []

    def test_load_nonexistent_directory(self):
        """Test loading from nonexistent directory creates it and returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "nonexistent"
            docs = load_documents(str(nonexistent))
            assert docs == []
            assert nonexistent.exists()

    def test_load_unsupported_files_ignored(self):
        """Test that unsupported file types are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create unsupported file
            unsupported_file = Path(tmpdir) / "test.jpg"
            unsupported_file.write_text("fake image content")

            docs = load_documents(tmpdir)
            assert len(docs) == 0

    def test_load_txt_file(self):
        """Test loading plain text file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = Path(tmpdir) / "test.txt"
            txt_file.write_text("This is test content.\nSecond line.")

            docs = load_documents(tmpdir)
            assert len(docs) == 1
            assert docs[0].page_content == "This is test content.\nSecond line."
            assert docs[0].metadata["source"] == str(txt_file)

    @patch('loader._DOCX_AVAILABLE', False)
    def test_load_docx_without_dependency(self):
        """Test loading DOCX file when dependency is not available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docx_file = Path(tmpdir) / "test.docx"
            docx_file.write_text("fake docx content")

            docs = load_documents(tmpdir)
            assert len(docs) == 0  # Should be skipped due to missing dependency

    def test_supported_extensions_defined(self):
        """Test that supported extensions are properly defined."""
        assert isinstance(SUPPORTED_EXTENSIONS, set)
        assert ".pdf" in SUPPORTED_EXTENSIONS
        assert ".txt" in SUPPORTED_EXTENSIONS
        assert ".docx" in SUPPORTED_EXTENSIONS
        # Should not contain common unsupported extensions
        assert ".jpg" not in SUPPORTED_EXTENSIONS
        assert ".png" not in SUPPORTED_EXTENSIONS


class TestLoadSingleFile:
    """Test loading individual files."""

    def test_load_txt_file_content(self):
        """Test loading content from TXT file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            f.flush()
            file_path = Path(f.name)

        try:
            docs = _load_single_file(file_path, ".txt")
            assert len(docs) == 1
            assert docs[0].page_content == "Test content"
            assert "source" in docs[0].metadata
        finally:
            safe_unlink(file_path)

    @patch('loader.PyPDFLoader')
    def test_load_pdf_file(self, mock_pdf_loader):
        """Test PDF loading uses correct loader."""
        mock_loader = Mock()
        mock_loader.load.return_value = [Document(page_content="PDF content", metadata={"page": 1})]
        mock_pdf_loader.return_value = mock_loader

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"fake pdf")
            f.flush()
            file_path = Path(f.name)

        try:
            docs = _load_single_file(file_path, ".pdf")
            assert len(docs) == 1
            assert docs[0].page_content == "PDF content"
            mock_pdf_loader.assert_called_once_with(str(file_path))
        finally:
            safe_unlink(file_path)

    def test_load_unsupported_extension_raises_error(self):
        """Test loading unsupported extension raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"content")
            f.flush()
            file_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="No loader for extension"):
                _load_single_file(file_path, ".xyz")
        finally:
            safe_unlink(file_path)

    @patch('loader._DOCX_AVAILABLE', True)
    @patch('loader.Docx2txtLoader')
    def test_load_docx_file_when_available(self, mock_docx_loader):
        """Test DOCX loading when dependency is available."""
        mock_loader = Mock()
        mock_loader.load.return_value = [Document(page_content="DOCX content")]
        mock_docx_loader.return_value = mock_loader

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            f.write(b"fake docx")
            f.flush()
            file_path = Path(f.name)

        try:
            docs = _load_single_file(file_path, ".docx")
            assert len(docs) == 1
            assert docs[0].page_content == "DOCX content"
        finally:
            safe_unlink(file_path)


class TestLoaderErrorHandling:
    """Test error handling in document loading."""

    @patch('loader.TextLoader')
    def test_loader_exception_handled(self, mock_text_loader):
        """Test that loader exceptions are caught and logged."""
        mock_loader = Mock()
        mock_loader.load.side_effect = Exception("Load failed")
        mock_text_loader.return_value = mock_loader

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("content")
            f.flush()
            file_path = Path(f.name)

        try:
            # Should not raise exception, just log error
            docs = load_documents(str(file_path.parent))
            # File should be skipped due to error
            assert len(docs) == 0
        finally:
            safe_unlink(file_path)

    @patch('loader.PyPDFLoader')
    def test_pdf_import_error_handled(self, mock_pdf_loader):
        """Test handling of missing PDF dependency."""
        mock_pdf_loader.side_effect = ImportError("PyPDF not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_file = Path(tmpdir) / "test.pdf"
            pdf_file.write_bytes(b"pdf content")

            docs = load_documents(tmpdir)
            assert len(docs) == 0  # Should be skipped