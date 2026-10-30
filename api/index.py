import os
import sys

# Ensure the root project directory is on sys.path so thelawala_search and web_app can be resolved
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from web_app import app
