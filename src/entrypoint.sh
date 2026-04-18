#!/bin/bash

# Start the Flask application in the background
python3 flaskapp.py &

# Start the Streamlit application
exec streamlit run main.py
