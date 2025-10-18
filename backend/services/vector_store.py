"""
Vector Store Manager
Handles semantic search and Q&A memory using FAISS
"""

import os
import logging
import pickle
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️  FAISS not installed. Run: pip install faiss-cpu")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleEmbeddings:
    """Simple embeddings using Groq or OpenAI"""
    
    def __init__(self, api_key: str, use_groq: bool = False):
        self.use_groq = use_groq
        
        if use_groq:
            from groq import Groq
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.3-70b-versatile"
        else:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = "text-embedding-ada-002"
    
    def embed_text(self, text: str) -> List[float]:
        """Create embeddings for text"""
        if self.use_groq:
            return self._simple_embedding(text)
        else:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Simple text embedding fallback"""
        import hashlib
        
        embedding = []
        for i in range(6):
            chunk = text[i*100:(i+1)*100] if len(text) > i*100 else text
            hash_val = int(hashlib.md5(chunk.encode()).hexdigest(), 16)
            for j in range(64):
                embedding.append(((hash_val >> j) & 1) * 2 - 1)
        
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding


class VectorStoreManager:
    """Manages vector storage and retrieval using FAISS"""
    
    def __init__(self, api_key: str, use_groq: bool = False, persist_dir: str = "vector_stores"):
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS not installed. Run: pip install faiss-cpu")
        
        self.embeddings = SimpleEmbeddings(api_key=api_key, use_groq=use_groq)
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(exist_ok=True)
        
        logger.info(f"✅ Vector Store Manager initialized (persist_dir: {persist_dir})")
    
    def create_report_vectorstore(self, report_id: str, report_text: str, metadata: Dict[str, Any]) -> bool:
        """Create and save a vector store for a report"""
        try:
            logger.info(f"Creating vector store for report: {report_id}")
            
            chunks = self._split_text(report_text)
            logger.info(f"Split into {len(chunks)} chunks")
            
            embeddings = []
            for i, chunk in enumerate(chunks):
                if i % 10 == 0:
                    logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                emb = self.embeddings.embed_text(chunk)
                embeddings.append(emb)
            
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            dimension = len(embeddings[0])
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings_array)
            
            store_path = self.persist_dir / f"{report_id}.faiss"
            metadata_path = self.persist_dir / f"{report_id}.pkl"
            
            faiss.write_index(index, str(store_path))
            
            with open(metadata_path, 'wb') as f:
                pickle.dump({'chunks': chunks, 'metadata': metadata}, f)
            
            logger.info(f"✅ Vector store saved: {store_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating vector store: {e}")
            return False
    
    def search_similar(self, report_id: str, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar chunks in a report"""
        try:
            store_path = self.persist_dir / f"{report_id}.faiss"
            metadata_path = self.persist_dir / f"{report_id}.pkl"
            
            if not store_path.exists():
                logger.warning(f"Vector store not found: {report_id}")
                return []
            
            index = faiss.read_index(str(store_path))
            
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                chunks = data['chunks']
                metadata = data['metadata']
            
            query_embedding = self.embeddings.embed_text(query)
            query_array = np.array([query_embedding], dtype=np.float32)
            
            distances, indices = index.search(query_array, min(k, len(chunks)))
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(chunks):
                    results.append({
                        'text': chunks[idx],
                        'score': float(distances[0][i]),
                        'chunk_index': int(idx),
                        'metadata': metadata
                    })
            
            logger.info(f"Found {len(results)} relevant chunks")
            return results
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def delete_vectorstore(self, report_id: str) -> bool:
        """Delete a vector store"""
        try:
            store_path = self.persist_dir / f"{report_id}.faiss"
            metadata_path = self.persist_dir / f"{report_id}.pkl"
            
            if store_path.exists():
                os.remove(store_path)
            if metadata_path.exists():
                os.remove(metadata_path)
            
            logger.info(f"Deleted vector store: {report_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting vector store: {e}")
            return False
    
    def _split_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks if chunks else [text]
