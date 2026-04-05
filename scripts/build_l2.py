from pathlib import Path
import subprocess
import shutil
def main(config):
    subprocess.run(["docker", "compose", "down"], check=True)
    if Path("dist").exists():
        shutil.rmtree("dist")
    subprocess.run(["python3", "-m", "gen"], check=True)
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
