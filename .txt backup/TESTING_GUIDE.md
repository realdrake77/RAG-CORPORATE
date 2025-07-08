# 🧪 Testing the New Pinecone-Only Implementation

## 🎯 Testing Strategy

Here's a complete guide to test your new Pinecone-only RAG chatbot implementation.

## 🔧 Prerequisites

### 1. **Environment Setup**
Make sure your `.env` file has valid API keys:
```bash
# Required
OPENAI_API_KEY=sk-proj-your-actual-key-here
PINECONE_API_KEY=pcsk_your-actual-pinecone-key-here
PINECONE_ENVIRONMENT=us-east-1-aws

# Optional
HF_TOKEN=your_huggingface_token_here
```

### 2. **Install Dependencies**
```bash
# Activate virtual environment (if using one)
venv\Scripts\activate

# Install/update dependencies
pip install -r requirements_fastapi.txt

# Verify Pinecone installation
python -c "import pinecone; print('Pinecone available')"
python -c "from langchain_pinecone import PineconeVectorStore; print('LangChain Pinecone available')"
```

## 🚀 Step-by-Step Testing

### **Step 1: Test Pinecone Vector Database**

Run this command to test the vector database independently:
```bash
python test_pinecone_db.py
```

### **Step 2: Test FastAPI Backend**

Start the FastAPI server:
```bash
uvicorn main:app --reload
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     ✅ All components initialized successfully
INFO:     ✅ Pinecone client initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### **Step 3: Test API Endpoints**

#### 3.1 Health Check
```bash
curl http://localhost:8000/api/status
```

Expected response:
```json
{
  "status": "healthy",
  "backend": "pinecone",
  "documents_indexed": 0,
  "queries_processed": 0,
  "avg_query_time": 0.0,
  "timestamp": "2025-06-28T..."
}
```

#### 3.2 Test Document Upload
```bash
# Windows (PowerShell)
Invoke-RestMethod -Uri "http://localhost:8000/api/upload" -Method Post -InFile "path\to\your\document.pdf" -ContentType "multipart/form-data"

# Or use the web interface at http://localhost:8000
```

#### 3.3 Test Chat Endpoint
```bash
curl -X POST "http://localhost:8000/api/chat" -H "Content-Type: application/json" -d "{\"message\": \"What is this document about?\", \"session_id\": \"test\"}"
```

### **Step 4: Test Web Interface**

1. **Open Browser**: Go to `http://localhost:8000`
2. **Upload Documents**: Drag & drop a PDF file
3. **Watch Progress**: Verify the progress bar works smoothly
4. **Send Messages**: Ask questions about your documents
5. **Check Metrics**: Verify query counter updates

## 🧪 Automated Tests

### **Test 1: Vector Database Test**
```bash
python test_pinecone_db.py
```

### **Test 2: Full Integration Test**
```bash
python test_integration.py
```

### **Test 3: API Performance Test**
```bash
python test_api_performance.py
```

## 🔍 What to Look For

### ✅ **Success Indicators**

1. **Startup**:
   - ✅ "Pinecone client initialized successfully"
   - ✅ "All components initialized successfully"
   - ✅ Server starts without errors

2. **Document Upload**:
   - ✅ Progress bar animates smoothly
   - ✅ "Upload Successful" toast notification
   - ✅ Documents counter updates
   - ✅ Chat input becomes enabled

3. **Chat Functionality**:
   - ✅ Typing indicator appears
   - ✅ Response generated with sources
   - ✅ Query counter increments
   - ✅ Response time displayed

4. **Pinecone Integration**:
   - ✅ Index created automatically
   - ✅ Vectors stored successfully
   - ✅ Search returns relevant results
   - ✅ Status shows "pinecone" backend

### ❌ **Potential Issues**

1. **API Key Problems**:
   ```
   ❌ PINECONE_API_KEY environment variable is not set
   ❌ Pinecone initialization failed
   ```
   **Solution**: Check your `.env` file

2. **Network Issues**:
   ```
   ❌ Failed to connect to Pinecone
   ❌ Index creation timeout
   ```
   **Solution**: Check internet connection and Pinecone service status

3. **Package Issues**:
   ```
   ❌ ImportError: No module named 'pinecone'
   ```
   **Solution**: `pip install -r requirements_fastapi.txt`

## 📊 Performance Benchmarks

### **Expected Performance**:
- **Document Upload**: 2-10 seconds for small PDFs
- **Index Creation**: 30-60 seconds (first time only)
- **Query Response**: 0.5-2 seconds
- **Vector Search**: <500ms

### **Monitoring**:
- Watch the system status panel for real-time metrics
- Check browser console for any JavaScript errors
- Monitor FastAPI logs for backend issues

## 🛠️ Troubleshooting

### **Common Issues**:

1. **"Vector store not initialized"**
   - Upload documents first before chatting

2. **"No documents provided"**
   - Ensure PDF files are valid and not empty

3. **"Pinecone API key not found"**
   - Check `.env` file exists and has correct key

4. **Progress bar not working**
   - Check browser console for JavaScript errors
   - Verify upload modal elements exist

5. **Query counter not updating**
   - Should increment immediately on message send
   - Check network tab for API call success

## 🎯 Testing Checklist

### **Basic Functionality**
- [ ] Server starts without errors
- [ ] API status endpoint returns healthy
- [ ] Web interface loads correctly
- [ ] File upload works with progress bar
- [ ] Chat functionality works
- [ ] Query counter updates
- [ ] Source citations appear

### **Pinecone Integration**
- [ ] Pinecone client initializes
- [ ] Index created automatically
- [ ] Documents indexed successfully
- [ ] Vector search returns results
- [ ] Status shows "pinecone" backend

### **UI/UX**
- [ ] Progress bar animates smoothly
- [ ] Toast notifications work
- [ ] Typing indicators appear
- [ ] Responsive design works
- [ ] Animations are smooth

### **Error Handling**
- [ ] Invalid file types rejected
- [ ] Large files rejected (>10MB)
- [ ] Network errors handled gracefully
- [ ] API errors displayed to user

## 🚀 Next Steps

After successful testing:

1. **Production Setup**:
   - Set up proper environment variables
   - Configure logging and monitoring
   - Set up backup and recovery

2. **Customization**:
   - Adjust embedding model if needed
   - Tune Pinecone index settings
   - Customize UI themes and branding

3. **Deployment**:
   - Deploy to cloud platform
   - Set up SSL certificates
   - Configure domain and DNS

---

**Happy Testing! 🎉**

If you encounter any issues, check the logs and feel free to ask for help.
