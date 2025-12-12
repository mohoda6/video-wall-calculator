#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
