import sys
import os
from dotenv import load_dotenv

# Add your project directory to the sys.path
# CHANGE 'yourusername' TO YOUR ACTUAL PYTHONANYWHERE USERNAME
project_home = '/home/yourusername/hackaton'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Load environment variables from .env file
load_dotenv(os.path.join(project_home, '.env'))

# Import the Flask app
from app import app as application
