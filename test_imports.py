import sys
print('using', sys.executable)
import embeddings, loader
print('embeddings attributes', [a for a in dir(embeddings) if not a.startswith('_')])
print('loader attributes', [a for a in dir(loader) if not a.startswith('_')])
from embeddings import load_vectorstore, get_retriever
from loader import load_documents
print('imports successful')
