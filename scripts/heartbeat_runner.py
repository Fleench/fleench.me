#!/usr/bin/env python3
import subprocess
from pathlib import Path
import json

def run_heartbeat():
    workspace = Path("/home/openclaw/.openclaw/workspace/fleench.me")
    
    # 1. Pull
    subprocess.run(["git", "pull", "origin", "main"], cwd=workspace, check=True)
    
    # 2. Build
    subprocess.run(["docker", "compose", "down"], cwd=workspace, check=True)
    dist = workspace / "dist"
    if dist.exists():
        import shutil
        shutil.rmtree(dist)
    subprocess.run(["./venv/bin/python3", "-m", "gen"], cwd=workspace, check=True)
    subprocess.run(["docker", "compose", "up", "-d"], cwd=workspace, check=True)
    
    # 3. Email Check (The Logic to implement)
    # We will trigger a separate script 'scripts/process_emails.py'
    subprocess.run(["./venv/bin/python3", "scripts/process_emails.py"], cwd=workspace, check=True)

if __name__ == "__main__":
    run_heartbeat()
EOF
