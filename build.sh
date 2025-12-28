#!/bin/bash
set -e

echo "Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "Verifying installations..."
python -c "import jobspy; print('✓ jobspy installed')"
python -c "import fastapi; print('✓ fastapi installed')"
python -c "import uvicorn; print('✓ uvicorn installed')"
python -c "import pandas; print('✓ pandas installed')"

echo "Build completed successfully!"
