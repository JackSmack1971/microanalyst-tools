import sys
import os

# Add the project root to sys.path to allow imports from src
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.microanalyst.main import main

if __name__ == "__main__":
    main()
