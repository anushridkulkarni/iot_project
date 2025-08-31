#!/bin/bash

# Change to the server directory
cd ~/passenger_counter_project/server || { echo "Server directory not found!"; exit 1; }

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip and install required packages
pip install --upgrade pip
pip install Flask flask-httpauth werkzeug

echo "Setup complete. To run the server, use:"
echo "source venv/bin/activate"
echo "python3 server.py"

