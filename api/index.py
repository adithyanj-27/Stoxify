import sys
import os

# Ensure project root is on sys.path for serverless module resolution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
