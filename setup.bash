#!/bin/bash

# Check if requirements.txt exists
if [ ! -f requirements.txt ]; then
    echo "requirements.txt not found!"
    exit 1
fi

# Install the requirements
echo "Installing requirements..."
pip install -r requirements.txt

echo "All requirements have been installed."
