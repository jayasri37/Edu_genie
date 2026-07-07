import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
os.chdir(root)

cmd = [sys.executable, '-m', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8000']
print('Starting EduGenie server...')
print('Open: http://localhost:8000')
subprocess.call(cmd)
