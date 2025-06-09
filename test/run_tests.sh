#!/bin/bash

# Use the specific Python interpreter from your conda environment
PYTHON_PATH="/c/Users/wrdha/anaconda3/envs/dev/python"

echo "Testing connection to Neo4j..."
"$PYTHON_PATH" test_connection.py 