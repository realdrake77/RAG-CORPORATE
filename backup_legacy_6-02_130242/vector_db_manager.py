"""
Enterprise Pinecone Vector Database Manager
Production-ready vector database solution for enterprise RAG systems
"""

import os
import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

# Core imports
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

# Pinecone imports
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

logger = logging.getLogger(__name__)

class EnterpriseVectorDB:
    """
    Enterprise-grade Pinecone vector database manager
    Optimized for production RAG applications
    """
    
    def __init__(self, 
                 index_name: str = "enterprise-rag",
                 embeddings: Optional[Embeddings] = None):
        """
        Initialize the Pinecone vector database manager
        
        Args:
            index_name: Name of the Pinecone index
            embeddings: Embedding model to use
        """
        self.backend = "pinecone"
        self.index_name = index_name
        self.embeddings = embeddings
        self.vectorstore = None
        self.retriever = None
        
        # Performance metrics
        self.metrics = {
            "documents_indexed": 0,
            "queries_processed": 0,
            "avg_query_time": 0.0,
            "last_updated": datetime.now(),
            "index_dimension": 384  # for all-MiniLM-L6-v2
        }
        
        # Initialize Pinecone client
        self.pc = None
        self._initialize_client()
        
        logger.info(f"✅ EnterpriseVectorDB initialized with Pinecone backend")
    
    def _initialize_client(self) -> bool:
        """Initialize Pinecone client"""
        try:
            api_key = os.getenv("PINECONE_API_KEY")
            
            if not api_key:
                raise ValueError("❌ PINECONE_API_KEY not found in environment variables")
            
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=api_key)
            logger.info("✅ Pinecone client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Pinecone client: {str(e)}")
            raise e
    
    def _ensure_index_exists(self) -> bool:
        """Ensure Pinecone index exists, create if not"""
        try:
            logger.info(f"🔍 Checking if index '{self.index_name}' exists...")
            
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            logger.info(f"📋 Existing indexes: {existing_indexes}")
            
            if self.index_name not in existing_indexes:
                logger.info(f"🔧 Creating new Pinecone index: {self.index_name}")
                
                try:
                    # Create index with appropriate dimensions
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=self.metrics["index_dimension"],
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud="aws",
                            region="us-east-1"
                        )
                    )
                    logger.info(f"✅ Index '{self.index_name}' creation initiated")
                    
                except Exception as create_error:
                    logger.error(f"❌ Failed to create index: {str(create_error)}")
                    # If index creation fails, try with a different name
                    import time
                    timestamp = int(time.time())
                    fallback_name = f"{self.index_name}-{timestamp}"
                    logger.info(f"🔄 Trying fallback index name: {fallback_name}")
                    
                    self.pc.create_index(
                        name=fallback_name,
                        dimension=self.metrics["index_dimension"],
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud="aws",
                            region="us-east-1"
                        )
                    )
                    self.index_name = fallback_name
                    logger.info(f"✅ Fallback index '{fallback_name}' created")
                
                # Wait for index to be ready with better error handling
                import time
                max_retries = 60  # Increased timeout
                for i in range(max_retries):
                    try:
                        index_desc = self.pc.describe_index(self.index_name)
                        if index_desc.status.ready:
                            logger.info(f"✅ Index '{self.index_name}' is ready!")
                            break
                    except Exception as desc_error:
                        logger.debug(f"Index not ready yet: {desc_error}")
                    
                    if i == max_retries - 1:
                        logger.warning(f"⚠️ Index taking longer than expected to be ready")
                        # Try to proceed anyway
                        break
                    
                    time.sleep(2)
                    if i % 10 == 0:  # Log every 20 seconds
                        logger.info(f"⏳ Waiting for index to be ready... ({i+1}/{max_retries})")
                
            else:
                logger.info(f"✅ Using existing Pinecone index: {self.index_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to ensure index exists: {str(e)}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            
            # Try to provide more helpful error messages
            if "unauthorized" in str(e).lower():
                logger.error("💡 This looks like an API key issue. Please check your Pinecone API key.")
            elif "quota" in str(e).lower() or "limit" in str(e).lower():
                logger.error("💡 This might be a quota/limit issue. Check your Pinecone plan limits.")
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                logger.error("💡 This might be a network connectivity issue.")
            
            return False
    
    def create_vectorstore(self, documents: List[Document]) -> bool:
        """
        Create and populate the Pinecone vector store with documents
        
        Args:
            documents: List of documents to index
            
        Returns:
            bool: Success status
        """
        try:
            start_time = datetime.now()
            logger.info(f"🔄 Creating Pinecone vector store with {len(documents)} documents...")
            
            # Ensure we have a valid client
            if not self.pc:
                logger.error("❌ Pinecone client not initialized")
                return False
            
            # Ensure index exists
            if not self._ensure_index_exists():
                logger.error("❌ Failed to ensure index exists")
                return False
            
            # Create Pinecone vector store with better error handling
            try:
                logger.info("🔄 Attempting PineconeVectorStore.from_documents...")
                self.vectorstore = PineconeVectorStore.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    index_name=self.index_name
                )
                logger.info("✅ PineconeVectorStore created successfully using from_documents")
                
            except Exception as vs_error:
                logger.warning(f"⚠️ from_documents failed: {str(vs_error)}")
                logger.info("🔄 Trying alternative approach with existing index...")
                
                try:
                    # Get the index directly
                    index = self.pc.Index(self.index_name)
                    logger.info(f"✅ Got index reference: {self.index_name}")
                    
                    # Create vector store from existing index
                    self.vectorstore = PineconeVectorStore(
                        index=index,
                        embedding=self.embeddings
                    )
                    logger.info("✅ PineconeVectorStore created from existing index")
                    
                    # Add documents in smaller batches to avoid timeouts
                    batch_size = 50  # Process in smaller batches
                    texts = [doc.page_content for doc in documents]
                    metadatas = [doc.metadata for doc in documents]
                    
                    logger.info(f"🔄 Adding {len(texts)} documents in batches of {batch_size}...")
                    
                    for i in range(0, len(texts), batch_size):
                        batch_texts = texts[i:i+batch_size]
                        batch_metas = metadatas[i:i+batch_size]
                        
                        logger.info(f"📦 Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
                        
                        self.vectorstore.add_texts(
                            texts=batch_texts, 
                            metadatas=batch_metas
                        )
                        
                        # Small delay between batches
                        import time
                        time.sleep(0.5)
                    
                    logger.info("✅ All documents added to Pinecone successfully")
                    
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback approach also failed: {str(fallback_error)}")
                    return False
            
            # Create optimized retriever
            try:
                self.retriever = self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={
                        "k": 6,  # Return top 6 most relevant documents
                        "include_metadata": True
                    }
                )
                logger.info("✅ Retriever created successfully")
                
            except Exception as retriever_error:
                logger.warning(f"⚠️ Retriever creation failed, using basic retriever: {str(retriever_error)}")
                self.retriever = self.vectorstore.as_retriever()
            
            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.metrics["documents_indexed"] = len(documents)
            self.metrics["last_updated"] = datetime.now()
            
            logger.info(f"✅ Pinecone vector store created with {len(documents)} documents in {processing_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create Pinecone vector store: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            
            # Provide helpful error messages
            if "api" in str(e).lower() and "key" in str(e).lower():
                logger.error("💡 This appears to be an API key issue. Please verify your Pinecone API key.")
            elif "quota" in str(e).lower() or "limit" in str(e).lower():
                logger.error("💡 You may have hit a quota limit. Check your Pinecone plan.")
            elif "dimension" in str(e).lower():
                logger.error("💡 This appears to be a dimension mismatch. Check your embedding model.")
            
            return False
    
    def get_retriever(self):
        """Get the retriever for the vector store"""
        if not self.retriever:
            raise ValueError("❌ Vector store not initialized. Call create_vectorstore() first.")
        return self.retriever
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status and metrics of the Pinecone database"""
        return {
            "backend": "pinecone",
            "index_name": self.index_name,
            "initialized": self.vectorstore is not None,
            "metrics": self.metrics,
            "enterprise_ready": True,
            "client_connected": self.pc is not None
        }
    
    def similarity_search(self, query: str, k: int = 6) -> List[Document]:
        """
        Perform high-performance similarity search
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        if not self.vectorstore:
            raise ValueError("❌ Vector store not initialized")
        
        start_time = datetime.now()
        results = self.vectorstore.similarity_search(query, k=k)
        
        # Update performance metrics
        query_time = (datetime.now() - start_time).total_seconds()
        self.metrics["queries_processed"] += 1
        self.metrics["avg_query_time"] = (
            (self.metrics["avg_query_time"] * (self.metrics["queries_processed"] - 1) + query_time) /
            self.metrics["queries_processed"]
        )
        
        logger.info(f"🔍 Pinecone similarity search completed in {query_time:.3f} seconds")
        return results
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get detailed Pinecone index statistics"""
        try:
            if not self.pc:
                return {"error": "Pinecone client not initialized"}
            
            index = self.pc.Index(self.index_name)
            stats = index.describe_index_stats()
            
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {}
            }
        except Exception as e:
            logger.error(f"❌ Failed to get index stats: {str(e)}")
            return {"error": str(e)}
