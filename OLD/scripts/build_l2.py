from pathlib import Path
import subprocess
import shutil
import sys

def main(config):
    print("Executing Level 2 Build within Venv...")
    subprocess.run(["docker", "compose", "down"], check=True)
    dist_dir = Path("dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    venv_python = str(Path("venv/bin/python3").absolute())
    subprocess.run([venv_python, "-m", "gen"], check=True)
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
