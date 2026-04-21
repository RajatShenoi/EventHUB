"""WSGI entry point for Gunicorn."""
import os
from dotenv import load_dotenv

# Load environment variables (optional, mainly for local development)
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
