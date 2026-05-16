#!/usr/bin/env python
"""
Wrapper script to run training with correct module paths
"""
import sys
import os

# Add backend directory to Python path so imports work
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Now import and run the training script
from models import train

if __name__ == '__main__':
    # Run training with command line arguments
    train.main()
