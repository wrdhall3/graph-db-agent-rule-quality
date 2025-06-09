#!/bin/bash
# Data Quality Rule Validation System Runner
# This script sets up the environment and runs the DQ validation workflow

echo "Starting Data Quality Rule Validation System..."
echo "=============================================="

# Activate conda environment
echo "Activating conda environment 'dev'..."
# Try different conda installation paths
if [ -f "/c/Users/wrdha/anaconda3/etc/profile.d/conda.sh" ]; then
    source /c/Users/wrdha/anaconda3/etc/profile.d/conda.sh
elif [ -f "/c/Users/wrdha/miniconda3/etc/profile.d/conda.sh" ]; then
    source /c/Users/wrdha/miniconda3/etc/profile.d/conda.sh
else
    echo "Conda not found in expected locations. Trying conda activate directly..."
fi
conda activate dev

# Check if activation was successful
if [ "$CONDA_DEFAULT_ENV" != "dev" ]; then
    echo "Failed to activate conda environment 'dev'"
    echo "Please ensure the environment exists and try again"
    exit 1
fi

echo "Conda environment activated: $CONDA_DEFAULT_ENV"
echo "Python version: $(python --version)"

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
    echo "Environment variables loaded from .env file"
else
    echo "No .env file found in current directory"
fi

# Check if OPENAI_API_KEY is now available
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY not set after loading .env file."
    echo "Please ensure your .env file contains: OPENAI_API_KEY=your-api-key-here"
    echo "Or set it manually with: export OPENAI_API_KEY='your-api-key-here'"
else
    echo "OPENAI_API_KEY is set and ready to use"
fi

# Check for required Python packages
echo "Checking dependencies..."
python -c "import crewai; print('CrewAI available')" 2>/dev/null || {
    echo "CrewAI not found. Installing..."
    pip install crewai crewai-tools
}

python -c "import mysql.connector; print('MySQL connector available')" 2>/dev/null || {
    echo "MySQL connector not found. Installing..."
    pip install mysql-connector-python
}

python -c "import neo4j; print('Neo4j driver available')" 2>/dev/null || {
    echo "Neo4j driver not found. Installing..."
    pip install neo4j
}

echo "Dependencies checked."
echo ""

# Run the DQ validation system
echo "Starting DQ validation system..."
python dq_main.py

echo ""
echo "DQ validation system completed." 