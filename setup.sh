#!/bin/bash

# Install Python dependencies from requirements.txt
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

# Download NLTK data (like 'punkt' for tokenization)
python -c "import nltk; nltk.download('punkt_tab')"

# You can add other NLTK resources if needed:
# python -c "import nltk; nltk.download('stopwords')"
# python -c "import nltk; nltk.download('averaged_perceptron_tagger')"

# Optional: Add any other setup steps (like setting environment variables)
