# Enterprise RAG Chatbot - Streamlit Version

A modern, enterprise-grade RAG (Retrieval-Augmented Generation) chatbot built with Streamlit, featuring a beautiful UI that matches your original design.

## 🚀 Features

- **Modern UI**: Custom CSS styling that replicates your original HTML/CSS/JS design
- **Document Processing**: Upload and process PDF documents for Q&A
- **Enterprise-grade**: Built with Pinecone vector database and OpenAI GPT-4
- **Real-time Chat**: Interactive chat interface with message history
- **Source Attribution**: Shows document sources for each response
- **System Metrics**: Real-time statistics and monitoring
- **Responsive Design**: Works on desktop and mobile devices

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Pinecone API key
- HuggingFace token (optional, for embeddings)

## 🛠️ Installation & Setup

### Option 1: Quick Start (Recommended)
```bash
# Navigate to the project directory
cd "/home/stark/Downloads/newui-ragenterprise-themes (5)/newui-ragenterprise-themes"

# Run the deployment script
./run_streamlit.sh
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements_streamlit.txt

# Run the application
streamlit run streamlit_app.py
```

## 🔧 Configuration

### Environment Variables
Make sure your `.env` file contains:

```env
OPENAI_API_KEY="your_openai_api_key_here"
HF_TOKEN="your_huggingface_token_here"
PINECONE_API_KEY="your_pinecone_api_key_here"
PINECONE_ENVIRONMENT="us-east-1"
PINECONE_INDEX_NAME="enterprise-rag-chatbot"
```

### Pinecone Setup
1. Create a Pinecone account at [pinecone.io](https://pinecone.io)
2. Create a new index with the following settings:
   - **Index Name**: `enterprise-rag-chatbot`
   - **Dimensions**: 384
   - **Metric**: Cosine
   - **Cloud Provider**: AWS
   - **Region**: us-east-1

## 🎨 UI Features

The Streamlit version includes:

- **Custom CSS**: Matches your original design with Inter font and modern styling
- **Dark/Light Mode Support**: CSS variables for easy theme switching
- **Responsive Layout**: Sidebar for controls, main area for chat
- **Status Indicators**: Real-time system status and metrics
- **File Upload**: Drag-and-drop style file upload area
- **Chat Interface**: Modern chat bubbles with user/assistant distinction
- **Source Display**: Expandable source citations for responses

## 📚 Usage

1. **Upload Documents**: Use the sidebar to upload PDF documents
2. **Process Documents**: Click "Process Documents" to index them
3. **Start Chatting**: Ask questions about your uploaded documents
4. **View Sources**: Expand the "Sources" section to see document citations
5. **Adjust Settings**: Use the sidebar to modify temperature and token limits

## 🔄 Migrating from FastAPI

If you were using the FastAPI version (`main.py`), this Streamlit version provides:

- ✅ Same backend logic and RAG functionality
- ✅ Same vector database and LLM components
- ✅ Equivalent document processing capabilities
- ✅ Similar UI design and user experience
- ✅ Real-time chat interface
- ❌ API endpoints (not needed for Streamlit)
- ❌ Static file serving (handled by Streamlit)

## 🚀 Deployment Options

### Local Development
```bash
streamlit run streamlit_app.py --server.port 8501
```

### Streamlit Cloud
1. Push your code to GitHub
2. Connect to [share.streamlit.io](https://share.streamlit.io)
3. Deploy directly from your repository
4. Add secrets in the Streamlit Cloud dashboard

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements_streamlit.txt .
RUN pip install -r requirements_streamlit.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Heroku Deployment
1. Create a `Procfile`:
   ```
   web: sh setup.sh && streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
   ```
2. Create `setup.sh`:
   ```bash
   mkdir -p ~/.streamlit/
   echo "[server]
   port = $PORT
   enableCORS = false
   headless = true
   " > ~/.streamlit/config.toml
   ```

## 🎛️ Customization

### Styling
Modify the CSS in the `load_custom_css()` function to customize:
- Colors and themes
- Typography
- Layout and spacing
- Animation effects

### Features
Add new features by:
- Extending the sidebar with new controls
- Adding new message types
- Implementing additional document loaders
- Integrating new LLM providers

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements_streamlit.txt
   ```

2. **API Key Issues**: Check your `.env` file and API key validity

3. **Pinecone Connection**: Verify your Pinecone API key and index name

4. **Memory Issues**: For large documents, consider:
   - Reducing chunk size
   - Processing documents in batches
   - Using a smaller embedding model

### Performance Optimization

- **Caching**: Uses `@st.cache_resource` for component initialization
- **Session State**: Maintains conversation history efficiently
- **Chunking**: Optimized document splitting for better retrieval
- **Streaming**: Real-time response display

## 📈 Monitoring

The application includes built-in metrics:
- Documents indexed count
- Queries processed count
- Average query processing time
- System status indicators

## 🤝 Contributing

Feel free to enhance the application by:
- Adding new document formats
- Implementing new UI features
- Optimizing performance
- Adding tests and documentation

## 📄 License

This project is part of your enterprise RAG system. Refer to your organization's licensing terms.

---

**Note**: This Streamlit version maintains all the functionality of your original FastAPI application while providing a more streamlined deployment process and enhanced user interface.
