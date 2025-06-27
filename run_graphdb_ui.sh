#!/bin/bash

# GraphDB Query UI Startup Script

echo "🚀 Starting GraphDB Query UI..."
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking required packages..."
python -c "import flask, neo4j, langchain_openai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: Required packages not installed. Please run:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded from .env"
else
    echo "⚠️  No .env file found. Create one with your OpenAI API key:"
    echo "   echo 'OPENAI_API_KEY=your-api-key-here' > .env"
fi

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY environment variable not set"
    echo "   Please either:"
    echo "   1. Create a .env file with: OPENAI_API_KEY=your-api-key-here"
    echo "   2. Or set it manually: export OPENAI_API_KEY='your-api-key-here'"
    echo ""
fi

# Check if Neo4j is accessible
echo "🔍 Testing Neo4j connection..."
python -c "
from neo4j_tools import Neo4jConnection
try:
    conn = Neo4jConnection()
    conn.connect()
    print('✅ Neo4j connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Neo4j connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Cannot connect to Neo4j. Please ensure:"
    echo "   1. Neo4j database is running"
    echo "   2. Connection settings in neo4j_tools.py are correct"
    echo "   3. Database contains the expected schema"
    exit 1
fi

echo ""
echo "✅ All checks passed!"
echo ""
echo "🌐 Starting GraphDB Query UI..."
echo "   URL: http://localhost:5050"
echo "   Press Ctrl+C to stop"
echo ""

# Start the Flask application
python graphdb_ui.py 