#!/usr/bin/env python3
"""
Development launcher for pySSM2 logger.

This script allows running the logger from the project root directory
by adding the necessary paths to sys.path for imports to work correctly.

For production deployment, use the Makefile which copies all files
to /etc/pySSM2/ where they can import each other directly.
"""

import sys
import os
import asyncio

# Add src and config directories to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'config'))

# Now import and run the logger
import logger

if __name__ == '__main__':
    try:
        asyncio.run(logger.main())
    except KeyboardInterrupt:
        pass
