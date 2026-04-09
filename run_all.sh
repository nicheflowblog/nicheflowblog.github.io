#!/bin/bash
# ============================================================
# NicheFlow — end-to-end daily pipeline
# Run manually:  bash ~/nicheflow/run_all.sh
# Cron (9am):    0 9 * * * /bin/bash /Users/alexrobles/nicheflow/run_all.sh
# ============================================================

set -euo pipefail

# ── Paths ────────────────────────────────────────────────────
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$REPO/deploy/logs/cron.log"
PYTHON="${PYTHON:-$(command -v python3 2>/dev/null || echo /Library/Frameworks/Python.framework/Versions/3.13/bin/python3)}"
DATE_STAMP=$(date '+%Y-%m-%d')

# Ensure cron has a sane PATH
export PATH="/usr/local/bin:/usr/bin:/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"

# ── Logging helper ───────────────────────────────────────────
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

# ── Load env vars (API keys etc.) ────────────────────────────
ENV_FILE="$REPO/deploy/.env"
if [ -f "$ENV_FILE" ]; then
    # shellcheck source=/dev/null
    set -a; source "$ENV_FILE"; set +a
fi

# ── Preflight checks ─────────────────────────────────────────
mkdir -p "$REPO/deploy/logs" "$REPO/deploy/posts" "$REPO/posts"
cd "$REPO"

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    log "ERROR: ANTHROPIC_API_KEY is not set. Add it to deploy/.env or export it before running."
    exit 1
fi

log "=========================================="
log "NicheFlow daily run started"
log "=========================================="

# ── Step 1: Generate new article(s) → deploy/posts/ ──────────
log "Step 1: Running generate.py ..."
if $PYTHON generate.py >> "$LOG" 2>&1; then
    log "Step 1 ✓ generate.py complete"
else
    log "Step 1 ✗ generate.py failed — aborting"
    exit 1
fi

# ── Step 2: Rebuild index → deploy/index.html ────────────────
log "Step 2: Running index.py ..."
if $PYTHON index.py >> "$LOG" 2>&1; then
    log "Step 2 ✓ index.py complete"
else
    log "Step 2 ✗ index.py failed — aborting"
    exit 1
fi

# ── Step 3: Copy deploy/index.html → ./index.html ────────────
log "Step 3: Syncing index.html to repo root ..."
cp deploy/index.html index.html
log "Step 3 ✓ index.html copied"

# ── Step 4: Copy new posts from deploy/posts/ → ./posts/ ─────
log "Step 4: Syncing new posts to ./posts/ ..."
NEW_COUNT=0
for f in deploy/posts/*.html; do
    dest="posts/$(basename "$f")"
    if [ ! -f "$dest" ] || [ "$f" -nt "$dest" ]; then
        cp "$f" "$dest"
        NEW_COUNT=$((NEW_COUNT + 1))
        log "  Copied: $(basename "$f")"
    fi
done
log "Step 4 ✓ $NEW_COUNT file(s) synced to ./posts/"

# ── Step 5: Copy sitemap ──────────────────────────────────────
log "Step 5: Syncing sitemap.xml ..."
if [ -f deploy/sitemap.xml ]; then
    cp deploy/sitemap.xml sitemap.xml
    log "Step 5 ✓ sitemap.xml copied"
else
    log "Step 5 — deploy/sitemap.xml not found, skipping"
fi

# ── Step 6: Git commit and push ───────────────────────────────
log "Step 6: Committing and pushing ..."
git -C "$REPO" add -A

if git -C "$REPO" diff --cached --quiet; then
    log "Step 6 — Nothing to commit, skipping push"
else
    git -C "$REPO" commit -m "auto: daily post $DATE_STAMP"
    if git -C "$REPO" push origin main >> "$LOG" 2>&1; then
        log "Step 6 ✓ Pushed to origin main"
    else
        log "Step 6 ✗ Push failed"
        exit 1
    fi
fi

log "=========================================="
log "Run complete"
log "=========================================="
