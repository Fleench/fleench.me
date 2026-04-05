import subprocess
import os

def run_build(level):
    if level == 1:
        subprocess.run(["python3", "-m", "gen"], check=True)
    elif level == 2:
        subprocess.run(["docker", "compose", "down"], check=True)
        if os.path.exists("dist"):
            import shutil
            shutil.rmtree("dist")
        subprocess.run(["python3", "-m", "gen"], check=True)
        subprocess.run(["docker", "compose", "up", "-d"], check=True)
    
    # Auto-commit logic
    subprocess.run(["git", "add", "dist/"], check=True)
    subprocess.run(["git", "commit", "-m", f"build: automated build level {level}"], check=True)
