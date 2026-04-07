#!/bin/bash
# NicheFlow daily automation runner
# Add to cron: 0 8 * * * /bin/bash /path/to/nicheflow/run_all.sh

set -e
cd "$(dirname "$0")"

export ANTHROPIC_API_KEY="your_actual_key_here"
export AMAZON_ASSOCIATE_TAG="your_tag_here"
export GITHUB_TOKEN="our_actual_token_here"
export GITHUB_REPO="https://github.com/nicheflowblog/nicheflow.github.io"

mkdir -p logs output/posts

echo "$(date): Starting NicheFlow run" >> logs/run.log

python generate.py && \
python sitemap.py && \
python publish.py && \
python ping.py

echo "$(date): Run complete" >> logs/run.log
