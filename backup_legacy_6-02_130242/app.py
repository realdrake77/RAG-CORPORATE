  ## Enterprise RAG Chatbot with Pinecone & OpenAI
import streamlit as st
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import os
import logging
from datetime import datetime

# Import our enterprise Pinecone vector database manager
from hybrid_vector_db import HybridVectorDB

from dotenv import load_dotenv
load_dotenv()

# Configure logging for enterprise environment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enterprise_chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
hf_token = os.getenv("HF_TOKEN")
pinecone_api_key = os.getenv("PINECONE_API_KEY")

if hf_token:
    os.environ['HF_TOKEN'] = hf_token

if not openai_api_key:
    st.error("OpenAI API key not found in environment variables. Please check your .env file.")
    st.stop()

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize Hybrid Vector Database (Pinecone with Chroma fallback)
vector_db = HybridVectorDB(
    index_name="enterprise-rag-chatbot",
    embeddings=embeddings
)

# Initialize OpenAI LLM
llm = ChatOpenAI(
    api_key=openai_api_key,
    model_name="gpt-4o-mini",  # Cost-effective and fast
    temperature=0.1,
    max_tokens=1000
)

## Set up Streamlit UI with Professional Styling
st.set_page_config(
    page_title="Enterprise RAG Chatbot",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .chat-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #dee2e6;
        color: #212529 !important;
    }
    .chat-container strong {
        color: #495057 !important;
    }
    .sidebar-content {
        background: #ffffff;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 0.25rem;
    }
    .status-online {
        background-color: #d4edda;
        color: #155724;
    }
    .status-processing {
        background-color: #fff3cd;
        color: #856404;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2a5298;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown("""
<div class="main-header">
    <h1>🏢 Enterprise RAG Chatbot</h1>
    <p>Secure Document Retrieval & AI-Powered Q&A System</p>
</div>
""", unsafe_allow_html=True)

# Log session start
logger.info(f"New session started at {datetime.now()}")

# SIDEBAR CONFIGURATION
with st.sidebar:
    st.markdown("### 🔧 Session Management")
    
    # Session ID with better styling
    session_id = st.text_input(
        "Session ID",
        value="default_session",
        help="Unique identifier for your chat session"
    )
    
    # Session controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear", use_container_width=True):
            if session_id in st.session_state.get('store', {}):
                del st.session_state.store[session_id]
                st.success("Cleared!")
    
    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.clear()
            st.success("Reset!")
    
    st.divider()
    
    # System Status
    st.markdown("### 📊 System Status")
    
    # Get Pinecone database status
    db_status = vector_db.get_status()
    
    # Status indicators
    st.markdown('<div class="status-badge status-online">🟢 OpenAI Connected</div>', unsafe_allow_html=True)
    st.markdown('<div class="status-badge status-online">🟢 Pinecone Enterprise</div>', unsafe_allow_html=True)
    
    # Enterprise metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Vector Database", "Pinecone")
    with col2:
        st.metric("Documents", db_status["metrics"]["documents_indexed"])
    
    # Performance metrics
    if db_status["metrics"]["queries_processed"] > 0:
        avg_time = db_status["metrics"]["avg_query_time"]
        st.metric("Avg Query Time", f"{avg_time:.3f}s")
    
    # Pinecone-specific stats
    try:
        index_stats = vector_db.get_index_stats()
        if "total_vector_count" in index_stats:
            st.metric("Total Vectors", index_stats["total_vector_count"])
    except:
        pass
    
    # Session metrics
    total_sessions = len(st.session_state.get('store', {}).keys())
    st.metric("Active Sessions", total_sessions)
    
    current_time = datetime.now().strftime("%H:%M:%S")
    st.metric("Current Time", current_time)
    
    st.divider()
    
    # Document Upload Section
    st.markdown("### 📁 Document Management")
    
    # File upload with improved styling
    uploaded_files = st.file_uploader(
        "Upload Documents",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
        help="Upload PDF, TXT, or DOCX files for analysis"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded")
        for file in uploaded_files:
            file_size = len(file.getvalue()) / 1024  # KB
            st.write(f"📄 {file.name} ({file_size:.1f} KB)")
    
    st.divider()
    
    # Settings
    st.markdown("### ⚙️ Advanced Settings")
    
    # Model settings
    temperature = st.slider("Response Creativity", 0.0, 1.0, 0.1, 0.1)
    max_tokens = st.slider("Max Response Length", 100, 2000, 1000, 100)
    
    # Chunk size for processing
    chunk_size = st.slider("Document Chunk Size", 1000, 10000, 5000, 1000)
    
    st.divider()
    
    # Help section
    with st.expander("ℹ️ Help & Tips"):
        st.markdown("""
        **How to use:**
        1. Upload your documents using the file uploader
        2. Wait for processing to complete
        3. Ask questions about your documents
        4. Use different sessions for different topics
        
        **Tips:**
        - Use specific questions for better answers
        - Upload related documents together
        - Clear sessions to start fresh
        """)

## Statefully manage chat history
if 'store' not in st.session_state:
    st.session_state.store = {}

# MAIN CONTENT AREA
if uploaded_files:
    # Processing indicator
    with st.spinner("🔄 Processing documents..."):
        documents = []
        for uploaded_file in uploaded_files:
            temppdf = f"./temp_{uploaded_file.name}"
            with open(temppdf, "wb") as file:
                file.write(uploaded_file.getvalue())
                file_name = uploaded_file.name

            loader = PyPDFLoader(temppdf)
            docs = loader.load()
            documents.extend(docs)
            
            # Clean up temp file
            os.remove(temppdf)

        # Split and create embeddings for the documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=500
        )
        splits = text_splitter.split_documents(documents)
        
        # Update LLM with sidebar settings
        llm = ChatOpenAI(
            api_key=openai_api_key,
            model_name="gpt-4o-mini",
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Create vector store using our enterprise manager
        success = vector_db.create_vectorstore(splits)
        
        if success:
            retriever = vector_db.get_retriever()
            st.success(f"✅ Documents processed successfully using Pinecone Enterprise")
            
            # Show processing metrics
            status = vector_db.get_status()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Documents Indexed", status["metrics"]["documents_indexed"])
            with col2:
                st.metric("Vector Database", "Pinecone")
            with col3:
                last_updated = status["metrics"]["last_updated"].strftime("%H:%M:%S")
                st.metric("Last Updated", last_updated)
                
            # Show Pinecone-specific stats
            try:
                index_stats = vector_db.get_index_stats()
                if index_stats and "total_vector_count" in index_stats:
                    st.info(f"📊 Pinecone Index Stats: {index_stats['total_vector_count']} vectors, {index_stats['dimension']} dimensions")
            except Exception as e:
                logger.debug(f"Could not fetch index stats: {e}")
        else:
            st.error("❌ Failed to process documents with Pinecone. Please check your API key and try again.")
            st.stop()

        contextualize_q_system_prompt=(
            "Given a chat history and the latest user question"
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", contextualize_q_system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )
        
        history_aware_retriever=create_history_aware_retriever(llm,retriever,contextualize_q_prompt)

        ## Answer question

        # Answer question
        system_prompt = (
                "You are an assistant for question-answering tasks. "
                "Use the following pieces of retrieved context to answer "
                "the question. If you don't know the answer, say that you "
                "don't know. Use three sentences maximum and keep the "
                "answer concise."
                "\n\n"
                "{context}"
            )
        qa_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )
        
        question_answer_chain=create_stuff_documents_chain(llm,qa_prompt)
        rag_chain=create_retrieval_chain(history_aware_retriever,question_answer_chain)

        def get_session_history(session:str)->BaseChatMessageHistory:
            if session_id not in st.session_state.store:
                st.session_state.store[session_id]=ChatMessageHistory()
            return st.session_state.store[session_id]
        
        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain, get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )

        # CHAT INTERFACE
        st.markdown("### 💬 Ask Questions About Your Documents")
        
        # Chat input with better styling
        user_input = st.text_input(
            "Your question:",
            placeholder="Ask anything about your uploaded documents...",
            key="user_input"
        )
        
        if user_input:
            with st.spinner("🤖 Generating response..."):
                session_history = get_session_history(session_id)
                
                try:
                    response = conversational_rag_chain.invoke(
                        {"input": user_input},
                        config={
                            "configurable": {"session_id": session_id}
                        }
                    )
                    
                    # Display response in a nice container
                    st.markdown("### 🤖 Assistant Response:")
                    with st.container():
                        st.markdown(f"""
                        <div class="chat-container">
                            <strong>Question:</strong> {user_input}<br>
                            <strong>Answer:</strong> {response['answer']}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Show sources if available
                    if 'context' in response:
                        with st.expander("📚 Source Documents"):
                            for i, doc in enumerate(response['context'][:3]):  # Show top 3 sources
                                st.write(f"**Source {i+1}:**")
                                st.write(doc.page_content[:300] + "...")
                                st.divider()
                    
                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
                    logger.error(f"Response generation error: {str(e)}")

        # Chat History Display (optional, can be hidden)
        if st.checkbox("Show Chat History", value=False):
            session_history = get_session_history(session_id)
            if session_history.messages:
                st.markdown("### 📜 Chat History")
                for i, message in enumerate(session_history.messages[-6:]):  # Show last 6 messages
                    if hasattr(message, 'content'):
                        message_type = "🧑 Human" if i % 2 == 0 else "🤖 Assistant"
                        st.write(f"**{message_type}:** {message.content}")

else:
    # Welcome screen when no files are uploaded
    st.markdown("""
    <div style="text-align: center; padding: 3rem; background: #f8f9fa; border-radius: 10px; margin: 2rem 0;">
        <h2>👋 Welcome to Enterprise RAG Chatbot</h2>
        <p style="font-size: 1.2rem; color: #6c757d;">
            Upload your documents using the sidebar to get started!
        </p>
        <div style="margin-top: 2rem;">
            <span class="status-badge status-online">� Powered by Pinecone Enterprise</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>� Enterprise Scale</h4>
            <p>Powered by Pinecone vector database for unlimited document processing</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>⚡ Lightning Fast</h4>
            <p>Sub-second query responses with enterprise-grade vector search</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>🎯 Production Ready</h4>
            <p>Built for enterprise workloads with OpenAI and Pinecone integration</p>
        </div>
        """, unsafe_allow_html=True)










