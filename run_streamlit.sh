#!/bin/bash

echo "🚀 Starting Enterprise RAG Chatbot (Streamlit Version)"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy .env file to the main directory if it exists in parent
if [ -f "../.env" ]; then
    cp ../.env .env
    echo "Environment file copied."
fi

# Run Streamlit app
echo "Starting Streamlit application..."
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0

echo "✅ Application is running at http://localhost:8501"
