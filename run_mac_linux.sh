echo "========================================"
echo "  Multi-PDF RAG - Quick Start (Mac/Linux)"
echo "========================================"
echo ""

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "Starting app at http://localhost:8501"
echo "Press Ctrl+C to stop."
echo ""
streamlit run app.py
