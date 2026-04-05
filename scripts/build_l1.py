from pathlib import Path
import subprocess
def main(config):
    subprocess.run(["python3", "-m", "gen"], check=True)
