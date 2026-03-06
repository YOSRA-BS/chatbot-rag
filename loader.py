# =============================================================================
# loader.py — Load documents from the documents/ folder
# Supports: PDF (.pdf), Word (.docx), plain text (.txt)
# =============================================================================

import os
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader

# Docx support is optional — only needed if you have .docx files
try:
    from langchain_community.document_loaders import Docx2txtLoader
    _DOCX_AVAILABLE = True
except ImportError:
    _DOCX_AVAILABLE = False

from config import DOCS_FOLDER

# File extensions we handle
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def load_documents(folder: str = DOCS_FOLDER) -> List[Document]:
    """
    Read every supported file in `folder` and return a flat list of
    LangChain Document objects.

    Each Document has:
        .page_content  → the raw text
        .metadata      → {"source": "path/to/file.pdf", "page": 0, ...}

    Unsupported file types are silently skipped.
    """
    folder_path = Path(folder)

    # Create the folder if it does not exist yet
    if not folder_path.exists():
        folder_path.mkdir(parents=True)
        print(f"[loader] Created '{folder}' — add your documents there and re-run.")
        return []

    # Collect only files (skip sub-directories)
    files = [f for f in folder_path.iterdir() if f.is_file()]
    if not files:
        print(f"[loader] '{folder}' is empty — add PDF/DOCX/TXT files and re-run.")
        return []

    all_docs: List[Document] = []

    for file in sorted(files):
        ext = file.suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            print(f"[loader] Skipping unsupported file: {file.name}")
            continue

        print(f"[loader] Reading: {file.name} ...", end=" ")

        try:
            docs = _load_single_file(file, ext)
            all_docs.extend(docs)
            print(f"OK ({len(docs)} page(s)/section(s))")

        except ImportError as e:
            print(f"SKIP — missing dependency: {e}")
        except Exception as e:
            print(f"ERROR — {e}")

    print(f"[loader] Total loaded: {len(all_docs)} document section(s) "
          f"from {len(files)} file(s).\n")
    return all_docs


def _load_single_file(file: Path, ext: str) -> List[Document]:
    """
    Pick the right loader for the file extension and return its documents.
    """
    if ext == ".pdf":
        loader = PyPDFLoader(str(file))

    elif ext == ".docx":
        if not _DOCX_AVAILABLE:
            raise ImportError("Run:  pip install docx2txt")
        loader = Docx2txtLoader(str(file))

    elif ext == ".txt":
        loader = TextLoader(str(file), encoding="utf-8")

    else:
        # Should never reach here because of the SUPPORTED_EXTENSIONS check
        raise ValueError(f"No loader for extension: {ext}")

    return loader.load()