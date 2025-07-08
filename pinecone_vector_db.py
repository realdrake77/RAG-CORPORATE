"""
Pinecone Vector Database Manager
Enterprise-grade vector database for RAG applications
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

# Core imports
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

# Pinecone imports
try:
    from langchain_pinecone import PineconeVectorStore
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    raise ImportError("Pinecone is required. Install with: pip install pinecone-client langchain-pinecone")

logger = logging.getLogger(__name__)

class PineconeVectorDB:
    """
    Pinecone vector database manager for enterprise RAG applications
    """
    
    def __init__(self, 
                 index_name: str = "enterprise-rag",
                 embeddings: Optional[Embeddings] = None,
                 dimension: int = 384,
                 cloud: str = "aws",
                 region: str = "us-east-1"):
        self.index_name = index_name
        self.embeddings = embeddings
        self.dimension = dimension
        self.cloud = cloud
        self.region = region
        self.vectorstore = None
        self.retriever = None
        self.backend = "pinecone"
        
        # Metrics
        self.metrics = {
            "documents_indexed": 0,
            "queries_processed": 0,
            "avg_query_time": 0.0,
            "last_updated": datetime.now()
        }
        
        # Initialize Pinecone
        self.pc = None
        self._init_pinecone()
    
    def _init_pinecone(self) -> None:
        """Initialize Pinecone client"""
        if not PINECONE_AVAILABLE:
            raise RuntimeError("Pinecone is not available. Please install pinecone-client and langchain-pinecone")
        
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key or "your_pinecone" in api_key.lower():
            raise ValueError("PINECONE_API_KEY environment variable is not set or is placeholder")
        
        try:
            self.pc = Pinecone(api_key=api_key)
            logger.info("✅ Pinecone client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Pinecone client: {str(e)}")
            raise RuntimeError(f"Pinecone initialization failed: {str(e)}")
    
    def _ensure_index_exists(self) -> None:
        """Ensure the Pinecone index exists, create if it doesn't"""
        try:
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"🔧 Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=self.cloud, 
                        region=self.region
                    )
                )
                
                # Wait for index to be ready
                import time
                logger.info("⏳ Waiting for index to be ready...")
                for i in range(60):  # Wait up to 2 minutes
                    try:
                        index_stats = self.pc.describe_index(self.index_name)
                        if index_stats.status.ready:
                            logger.info("✅ Index is ready")
                            break
                        time.sleep(2)
                    except Exception as e:
                        if i == 59:  # Last attempt
                            raise RuntimeError(f"Index creation timeout: {str(e)}")
                        time.sleep(2)
            else:
                logger.info(f"✅ Pinecone index '{self.index_name}' already exists")
                
        except Exception as e:
            logger.error(f"❌ Failed to ensure index exists: {str(e)}")
            raise RuntimeError(f"Index creation/verification failed: {str(e)}")
    
    def create_vectorstore(self, documents: List[Document]) -> bool:
        """Create Pinecone vector store"""
        try:
            if not documents:
                raise ValueError("No documents provided")
            
            if not self.embeddings:
                raise ValueError("Embeddings not configured")
            
            # Ensure index exists
            self._ensure_index_exists()
            
            logger.info(f"🔄 Creating Pinecone vector store with {len(documents)} documents...")
            
            # Create vector store
            self.vectorstore = PineconeVectorStore.from_documents(
                documents=documents,
                embedding=self.embeddings,
                index_name=self.index_name
            )
            
            self.retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": 4}  # Return top 4 most relevant chunks
            )
            
            # Update metrics
            self.metrics["documents_indexed"] = len(documents)
            self.metrics["last_updated"] = datetime.now()
            
            logger.info(f"✅ Pinecone vector store created successfully with {len(documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pinecone vector store creation failed: {str(e)}")
            raise RuntimeError(f"Vector store creation failed: {str(e)}")
    
    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to existing vector store"""
        try:
            if not self.vectorstore:
                raise ValueError("Vector store not initialized. Call create_vectorstore first.")
            
            if not documents:
                logger.warning("No documents provided to add")
                return True
            
            logger.info(f"🔄 Adding {len(documents)} documents to existing vector store...")
            
            self.vectorstore.add_documents(documents)
            
            # Update metrics
            self.metrics["documents_indexed"] += len(documents)
            self.metrics["last_updated"] = datetime.now()
            
            logger.info(f"✅ Added {len(documents)} documents successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents: {str(e)}")
            raise RuntimeError(f"Adding documents failed: {str(e)}")
    
    def clear_index(self) -> bool:
        """Clear all vectors from the Pinecone index"""
        try:
            logger.info(f"🧹 Clearing all vectors from index: {self.index_name}")
            
            # Ensure index exists first
            self._ensure_index_exists()
            
            # Get the index
            index = self.pc.Index(self.index_name)
            
            # Delete all vectors using the correct syntax
            index.delete(delete_all=True)
            
            # Reset vector store and retriever
            self.vectorstore = None
            self.retriever = None
            
            # Reset metrics
            self.metrics["documents_indexed"] = 0
            self.metrics["last_updated"] = datetime.now()
            
            logger.info("✅ Index cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear index: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            logger.error(f"❌ Error details: {str(e)}")
            return False
    
    def replace_documents(self, documents: List[Document]) -> bool:
        """Replace all documents in the vector store with new ones"""
        try:
            if not documents:
                raise ValueError("No documents provided")
            
            if not self.embeddings:
                raise ValueError("Embeddings not configured")
            
            # Ensure index exists
            self._ensure_index_exists()
            
            # Clear existing documents
            logger.info("🧹 Clearing existing documents...")
            if not self.clear_index():
                logger.warning("⚠️ Failed to clear index, proceeding anyway...")
            
            # Add new documents
            logger.info(f"🔄 Adding {len(documents)} new documents...")
            
            # Create fresh vector store
            self.vectorstore = PineconeVectorStore.from_documents(
                documents=documents,
                embedding=self.embeddings,
                index_name=self.index_name
            )
            
            self.retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": 4}  # Return top 4 most relevant chunks
            )
            
            # Update metrics
            self.metrics["documents_indexed"] = len(documents)
            self.metrics["last_updated"] = datetime.now()
            
            logger.info(f"✅ Successfully replaced all documents with {len(documents)} new documents")
            return True
            
        except Exception as e:
            logger.error(f"❌ Document replacement failed: {str(e)}")
            raise RuntimeError(f"Document replacement failed: {str(e)}")
    
    def get_retriever(self):
        """Get retriever for the vector store"""
        if not self.retriever:
            raise ValueError("Vector store not initialized. Call create_vectorstore first.")
        return self.retriever
    
    def search(self, query: str, k: int = 4) -> List[Document]:
        """Search for similar documents"""
        try:
            if not self.vectorstore:
                raise ValueError("Vector store not initialized")
            
            start_time = datetime.now()
            results = self.vectorstore.similarity_search(query, k=k)
            end_time = datetime.now()
            
            # Update metrics
            query_time = (end_time - start_time).total_seconds()
            self.metrics["queries_processed"] += 1
            
            # Update average query time
            if self.metrics["queries_processed"] == 1:
                self.metrics["avg_query_time"] = query_time
            else:
                self.metrics["avg_query_time"] = (
                    (self.metrics["avg_query_time"] * (self.metrics["queries_processed"] - 1) + query_time) 
                    / self.metrics["queries_processed"]
                )
            
            logger.info(f"🔍 Search completed in {query_time:.3f}s, found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}")
            raise RuntimeError(f"Search failed: {str(e)}")
    
    def delete_index(self) -> bool:
        """Delete the Pinecone index (use with caution)"""
        try:
            logger.warning(f"🗑️ Deleting Pinecone index: {self.index_name}")
            self.pc.delete_index(self.index_name)
            
            # Reset state
            self.vectorstore = None
            self.retriever = None
            self.metrics["documents_indexed"] = 0
            
            logger.info(f"✅ Index '{self.index_name}' deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete index: {str(e)}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        try:
            index = self.pc.Index(self.index_name)
            stats = index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
        except Exception as e:
            logger.error(f"❌ Failed to get index stats: {str(e)}")
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information"""
        index_stats = self.get_index_stats()
        
        return {
            "backend": self.backend,
            "index_name": self.index_name,
            "dimension": self.dimension,
            "cloud": self.cloud,
            "region": self.region,
            "initialized": self.vectorstore is not None,
            "pinecone_available": PINECONE_AVAILABLE,
            "metrics": self.metrics,
            "index_stats": index_stats
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Check if client is working
            indexes = self.pc.list_indexes()
            
            # Check if our index exists and is ready
            index_exists = self.index_name in [idx.name for idx in indexes]
            index_ready = False
            
            if index_exists:
                index_info = self.pc.describe_index(self.index_name)
                index_ready = index_info.status.ready
            
            return {
                "status": "healthy" if index_ready else "degraded",
                "pinecone_client": "connected",
                "index_exists": index_exists,
                "index_ready": index_ready,
                "vector_store_initialized": self.vectorstore is not None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
