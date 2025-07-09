"""
Enterprise RAG Chatbot - Streamlit Version
Modern UI with custom CSS styling to match your original design
"""

import streamlit as st
import os
import logging
import tempfile
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import base64

# Import existing components
try:
    from pinecone_vector_db import PineconeVectorDB
except ImportError as e:
    st.error(f"❌ Failed to import PineconeVectorDB: {e}")
    st.stop()

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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Enterprise RAG Chatbot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to match your original design
def load_custom_css():
    st.markdown("""
    <style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');
    
    /* Root variables */
    :root {
        --primary-500: #3b82f6;
        --primary-600: #2563eb;
        --primary-700: #1d4ed8;
        --success-500: #22c55e;
        --warning-500: #f59e0b;
        --error-500: #ef4444;
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --border-color: #e2e8f0;
    }
    
    /* Dark mode */
    .dark {
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --border-color: #334155;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .stApp {
        background: var(--bg-secondary);
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling */
    .main-header {
        background: var(--bg-primary);
        padding: 1.5rem 2rem;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 1rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .logo {
        width: 3rem;
        height: 3rem;
        background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
        border-radius: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.5rem;
    }
    
    .logo-text h1 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    .logo-text p {
        margin: 0;
        font-size: 0.875rem;
        color: var(--text-secondary);
    }
    
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.2);
        border-radius: 0.5rem;
        color: var(--success-500);
        font-weight: 500;
    }
    
    .status-dot {
        width: 0.5rem;
        height: 0.5rem;
        background: var(--success-500);
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Chat container */
    .chat-container {
        background: var(--bg-primary);
        border-radius: 0.75rem;
        padding: 1.5rem;
        min-height: 500px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    /* Message styling */
    .message {
        margin-bottom: 1rem;
        padding: 1rem;
        border-radius: 0.75rem;
        max-width: 80%;
    }
    
    .user-message {
        background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
        color: white;
        margin-left: auto;
        margin-right: 0;
    }
    
    .assistant-message {
        background: var(--bg-secondary);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed var(--border-color);
        border-radius: 0.75rem;
        padding: 2rem;
        text-align: center;
        background: var(--bg-secondary);
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: var(--primary-500);
        background: rgba(59, 130, 246, 0.05);
    }
    
    /* Metrics cards */
    .metric-card {
        background: var(--bg-primary);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid var(--border-color);
        text-align: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-500);
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: var(--bg-primary);
    }
    
    /* Success/Error styling */
    .success-message {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.2);
        color: var(--success-500);
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    .error-message {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.2);
        color: var(--error-500);
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'documents_uploaded' not in st.session_state:
        st.session_state.documents_uploaded = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = ChatMessageHistory()
    if 'processing_stats' not in st.session_state:
        st.session_state.processing_stats = {
            'documents_indexed': 0,
            'queries_processed': 0,
            'avg_query_time': 0.0
        }

# Initialize components
@st.cache_resource
def initialize_components():
    """Initialize all the RAG components"""
    try:
        # Load API keys
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("OpenAI API key not found in environment variables")
            return None, None, None
        
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Initialize vector database
        vector_db = PineconeVectorDB(
            index_name=os.getenv("PINECONE_INDEX_NAME", "enterprise-rag-chatbot"),
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
        return embeddings, vector_db, llm
        
    except Exception as e:
        st.error(f"Failed to initialize components: {str(e)}")
        return None, None, None

# Create RAG chain
def create_rag_chain(llm, vector_db):
    """Create the RAG chain for question answering"""
    try:
        # Check if vector_db has a retriever available
        retriever = vector_db.get_retriever()
        if retriever is None:
            return None  # Return None if no retriever is available yet
        
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
            llm, retriever, contextualize_q_prompt
        )
        
        # Answer question prompt
        qa_system_prompt = """You are an enterprise AI assistant with access to company documents. 
        Provide accurate, professional responses based on the retrieved context. 
        Include source information when relevant.

        Context: {context}"""
        
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        # Create document chain
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        
        # Create RAG chain
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        # Add message history
        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            lambda session_id: st.session_state.chat_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        
        return conversational_rag_chain
        
    except Exception as e:
        st.error(f"Failed to create RAG chain: {str(e)}")
        return None

# Process uploaded documents
def process_documents(uploaded_files, vector_db):
    """Process and index uploaded documents"""
    if not uploaded_files:
        return False
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        all_docs = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            progress_bar.progress((i / len(uploaded_files)) * 0.8)
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            try:
                # Load and split document
                loader = PyPDFLoader(tmp_file_path)
                pages = loader.load()
                
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len,
                    separators=["\n\n", "\n", " ", ""]
                )
                
                docs = text_splitter.split_documents(pages)
                all_docs.extend(docs)
                
            finally:
                # Clean up temporary file
                os.unlink(tmp_file_path)
        
        # Index documents
        status_text.text("Indexing documents in vector database...")
        progress_bar.progress(0.9)
        
        # Check if vectorstore exists, if not create it, otherwise add documents
        if not hasattr(vector_db, 'vectorstore') or vector_db.vectorstore is None:
            # First time indexing - create vectorstore
            vector_db.create_vectorstore(all_docs)
        else:
            # Add to existing vectorstore
            vector_db.add_documents(all_docs)
        
        progress_bar.progress(1.0)
        status_text.text("✅ Documents processed successfully!")
        
        # Update stats
        st.session_state.processing_stats['documents_indexed'] += len(all_docs)
        st.session_state.documents_uploaded = True
        
        # Recreate RAG chain with updated vector database
        st.session_state.rag_chain = create_rag_chain(st.session_state.llm, vector_db)
        
        return True
        
    except Exception as e:
        st.error(f"Failed to process documents: {str(e)}")
        return False

# Main header
def render_header():
    st.markdown("""
    <div class="main-header">
        <div class="header-content">
            <div class="logo-section">
                <div class="logo">
                    <i class="fas fa-brain"></i>
                </div>
                <div class="logo-text">
                    <h1>Enterprise RAG</h1>
                    <p>AI-Powered Document Assistant</p>
                </div>
            </div>
            <div class="status-indicator">
                <div class="status-dot"></div>
                <span>Online</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main application
def main():
    # Load custom CSS
    load_custom_css()
    
    # Initialize session state
    init_session_state()
    
    # Render header
    render_header()
    
    # Initialize components
    if not st.session_state.initialized:
        with st.spinner("Initializing Enterprise RAG system..."):
            embeddings, vector_db, llm = initialize_components()
            
            if embeddings and vector_db and llm:
                st.session_state.embeddings = embeddings
                st.session_state.vector_db = vector_db
                st.session_state.llm = llm
                st.session_state.rag_chain = create_rag_chain(llm, vector_db)  # May be None initially
                st.session_state.initialized = True
                st.rerun()
            else:
                st.error("Failed to initialize system. Please check your API keys and try again.")
                return
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 System Status")
        
        # Metrics
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{st.session_state.processing_stats['documents_indexed']}</div>
                <div class="metric-label">Documents</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{st.session_state.processing_stats['queries_processed']}</div>
                <div class="metric-label">Queries</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Document upload
        st.markdown("### 📄 Document Upload")
        uploaded_files = st.file_uploader(
            "Upload PDF documents",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload PDF documents to enable Q&A functionality"
        )
        
        if uploaded_files and st.button("Process Documents", use_container_width=True):
            if process_documents(uploaded_files, st.session_state.vector_db):
                st.success("Documents processed successfully!")
                time.sleep(1)
                st.rerun()
        
        st.markdown("---")
        
        # Settings
        st.markdown("### ⚙️ Settings")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.1)
        max_tokens = st.slider("Max Tokens", 100, 2000, 1000, 100)
        
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_history = ChatMessageHistory()
            st.rerun()
        
        if st.button("🔄 Clear Cache & Restart", use_container_width=True):
            st.cache_resource.clear()
            st.session_state.clear()
            st.rerun()
    
    # Main chat interface
    st.markdown("### 💬 Chat Interface")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and "sources" in message:
                    with st.expander("Sources"):
                        for source in message["sources"]:
                            st.write(f"- {source}")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        if not st.session_state.documents_uploaded:
            st.warning("Please upload and process documents first!")
            return
        
        if not st.session_state.rag_chain:
            st.warning("RAG system not ready. Please upload documents first!")
            return
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    start_time = time.time()
                    
                    # Update LLM settings
                    st.session_state.llm.temperature = temperature
                    st.session_state.llm.max_tokens = max_tokens
                    
                    # Get response
                    response = st.session_state.rag_chain.invoke(
                        {"input": prompt},
                        config={"configurable": {"session_id": "default"}}
                    )
                    
                    processing_time = time.time() - start_time
                    
                    # Update stats
                    st.session_state.processing_stats['queries_processed'] += 1
                    current_avg = st.session_state.processing_stats['avg_query_time']
                    query_count = st.session_state.processing_stats['queries_processed']
                    st.session_state.processing_stats['avg_query_time'] = (
                        (current_avg * (query_count - 1) + processing_time) / query_count
                    )
                    
                    # Display response
                    st.markdown(response["answer"])
                    
                    # Extract sources
                    sources = []
                    if "context" in response:
                        for doc in response["context"]:
                            if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                                sources.append(doc.metadata['source'])
                    
                    # Add assistant message
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response["answer"],
                        "sources": sources
                    })
                    
                    # Show sources
                    if sources:
                        with st.expander("Sources"):
                            for source in set(sources):  # Remove duplicates
                                st.write(f"- {source}")
                
                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")

if __name__ == "__main__":
    main()
