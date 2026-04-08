#!/bin/bash
# NicheFlow daily automation runner
# Add to cron: 0 8 * * * /bin/bash /path/to/nicheflow/run_all.sh

set -e
cd "$(dirname "$0")"

export ANTHROPIC_API_KEY="sk-ant-YOUR_KEY_HERE"
export AMAZON_ASSOCIATE_TAG="yoursite-20"
export GITHUB_TOKEN="ghp_YOUR_TOKEN"
export GITHUB_REPO="yourusername/yourusername.github.io"

mkdir -p logs output/posts

echo "$(date): Starting NicheFlow run" >> logs/run.log

python generate.py && \
python sitemap.py && \
python publish.py && \
python ping.py

echo "$(date): Run complete" >> logs/run.log
