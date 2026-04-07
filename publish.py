import os
import subprocess
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    filename='logs/run.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
log = logging.getLogger(__name__)

GITHUB_REPO = os.environ.get('GITHUB_REPO', 'alexroblesr/alexroblesr.github.io')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
OUTPUT_DIR = Path('output')


def run(cmd, cwd=None):
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
    return result.stdout.strip()


def publish():
    log.info("Starting publish to GitHub Pages")

    deploy_dir = Path('deploy')

    if not deploy_dir.exists():
        log.info("Cloning repo for first time")
        token_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
        run(f"git clone {token_url} deploy")
    else:
        run("git pull", cwd='deploy')

    import shutil
    if OUTPUT_DIR.exists():
        for item in OUTPUT_DIR.iterdir():
            dest = deploy_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    run("git config user.email 'bot@nicheflow.local'", cwd='deploy')
    run("git config user.name 'NicheFlow Bot'", cwd='deploy')
    run("git add -A", cwd='deploy')

    status = run("git status --porcelain", cwd='deploy')
    if not status:
        log.info("Nothing to commit — no new articles")
        print("Nothing new to publish")
        return

    run(f'git commit -m "Auto-publish: {timestamp}"', cwd='deploy')
    run("git push", cwd='deploy')

    log.info("Published successfully to GitHub Pages")
    print(f"Published successfully at {timestamp}")


if __name__ == '__main__':
    publish()
