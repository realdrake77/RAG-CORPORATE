"""
Enterprise RAG Chatbot FastAPI Backend
Modern API server for HTML/CSS/JS frontend
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
import asyncio
import json
from datetime import datetime
import tempfile
import shutil

# Import existing components
from pinecone_vector_db import PineconeVectorDB
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enterprise_chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Enterprise RAG Chatbot API",
    description="Production-ready RAG chatbot with modern UI",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"
    temperature: float = 0.1
    max_tokens: int = 1000

class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    session_id: str
    timestamp: str
    processing_time: float

class SystemStatus(BaseModel):
    backend: str
    documents_indexed: int
    queries_processed: int
    avg_query_time: float
    last_updated: str
    status: str

# Global variables
embeddings = None
vector_db = None
llm = None
store = {}

# Initialize components
def initialize_components():
    global embeddings, vector_db, llm
    
    # Load API keys
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OpenAI API key not found")
    
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Initialize vector database
    vector_db = PineconeVectorDB(
        index_name="enterprise-rag-chatbot",
        embeddings=embeddings
    )
    
    # Initialize LLM
    llm = ChatOpenAI(
        api_key=openai_api_key,
        model_name="gpt-4o-mini",
        temperature=0.1,
        max_tokens=1000
    )
    
    logger.info("✅ All components initialized successfully")

# Chat session management
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Create RAG chain
def create_rag_chain():
    # Contextualize question prompt
    contextualize_q_system_prompt = """Given a chat history and the latest user question 
    which might reference context in the chat history, formulate a standalone question 
    which can be understood without the chat history. Do NOT answer the question, 
    just reformulate it if needed and otherwise return it as is."""
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    # Create history-aware retriever
    history_aware_retriever = create_history_aware_retriever(
        llm, vector_db.get_retriever(), contextualize_q_prompt
    )
    
    # Answer question prompt
    qa_system_prompt = """You are an enterprise AI assistant with access to company documents. 
    Provide accurate, professional responses based on the retrieved context. 
    Include source information when relevant.

    {context}"""
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    # Create question answer chain
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # Create retrieval chain
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    # Add message history
    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )
    
    return conversational_rag_chain

# Startup event
@app.on_event("startup")
async def startup_event():
    try:
        initialize_components()
        logger.info("🚀 Enterprise RAG Chatbot API started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize: {str(e)}")
        raise e

# Serve main HTML page
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <body>
                <h1>Enterprise RAG Chatbot</h1>
                <p>Frontend files not found. Please check the static directory.</p>
            </body>
        </html>
        """

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# System status
@app.get("/api/status")
async def get_system_status():
    if not vector_db:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    status = vector_db.get_status()
    return {
        "backend": status["backend"],
        "documents_indexed": status["metrics"]["documents_indexed"],
        "queries_processed": status["metrics"]["queries_processed"],
        "avg_query_time": status["metrics"]["avg_query_time"],
        "last_updated": status["metrics"]["last_updated"].isoformat(),
        "status": "online"
    }

# Chat endpoint
@app.post("/api/chat")
async def chat(chat_message: ChatMessage):
    if not vector_db or not vector_db.vectorstore:
        raise HTTPException(
            status_code=400, 
            detail="No documents uploaded. Please upload documents first."
        )
    
    try:
        start_time = datetime.now()
        
        # Create RAG chain
        rag_chain = create_rag_chain()
        
        # Update LLM parameters
        global llm
        llm.temperature = chat_message.temperature
        llm.max_tokens = chat_message.max_tokens
        
        # Process the message
        response = rag_chain.invoke(
            {"input": chat_message.message},
            config={"configurable": {"session_id": chat_message.session_id}}
        )
        
        # Extract sources
        sources = []
        if "context" in response:
            for doc in response["context"]:
                sources.append({
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                })
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "response": response["answer"],
            "sources": sources,
            "session_id": chat_message.session_id,
            "timestamp": datetime.now().isoformat(),
            "processing_time": processing_time
        }
        
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Document upload endpoint
@app.post("/api/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    if not vector_db:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        start_time = datetime.now()
        all_documents = []
        
        # Process each file
        for file in files:
            if file.content_type == "application/pdf":
                # Save temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    shutil.copyfileobj(file.file, temp_file)
                    temp_path = temp_file.name
                
                # Load and process PDF
                loader = PyPDFLoader(temp_path)
                documents = loader.load()
                
                # Split documents
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                splits = text_splitter.split_documents(documents)
                
                # Add metadata
                for doc in splits:
                    doc.metadata["source"] = file.filename
                    doc.metadata["upload_time"] = datetime.now().isoformat()
                
                all_documents.extend(splits)
                
                # Clean up temp file
                os.unlink(temp_path)
            
            else:
                logger.warning(f"Unsupported file type: {file.content_type}")
        
        if not all_documents:
            raise HTTPException(status_code=400, detail="No valid documents found")
        
        # Replace documents in vector store (clears old documents first)
        logger.info(f"🔄 Replacing vector store with {len(all_documents)} new documents...")
        success = vector_db.replace_documents(all_documents)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to replace documents in vector store")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": True,
            "message": f"Successfully processed {len(all_documents)} document chunks",
            "documents_processed": len(all_documents),
            "processing_time": processing_time
        }
        
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get chat sessions
@app.get("/api/sessions")
async def get_sessions():
    return {"sessions": list(store.keys())}

# Clear session
@app.delete("/api/sessions/{session_id}")
async def clear_session(session_id: str):
    if session_id in store:
        del store[session_id]
        return {"message": f"Session {session_id} cleared"}
    return {"message": "Session not found"}

# Clear documents endpoint
@app.delete("/api/documents")
async def clear_documents():
    """Clear all documents from the vector database"""
    if not vector_db:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        logger.info("🧹 API request to clear all documents")
        
        # Check if vector store exists
        if not vector_db.vectorstore:
            logger.info("ℹ️ No vector store initialized, nothing to clear")
            return {
                "success": True,
                "message": "No documents to clear - vector store not initialized"
            }
        
        # Attempt to clear the index
        success = vector_db.clear_index()
        
        if success:
            logger.info("✅ Documents cleared successfully via API")
            return {
                "success": True,
                "message": "All documents cleared successfully"
            }
        else:
            logger.error("❌ Failed to clear documents - clear_index returned False")
            raise HTTPException(
                status_code=500, 
                detail="Failed to clear documents from Pinecone index"
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Clear documents API error: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal error while clearing documents: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
