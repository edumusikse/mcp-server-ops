#!/bin/bash
# End-to-end deploy pipeline timing test.
# Proves git push to onyx bare repo is fast (target < 3000ms).
# Run: bash tests/test_deploy_pipeline.sh [iterations]
# Note: server_config_sync timing is tested separately via MCP (see CI notes below).

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)/server-config"
MARKER="$REPO_DIR/.pipeline-test-marker"
ITERATIONS="${1:-3}"
MAX_PUSH_MS=3000
PASS=0
FAIL=0

echo "=== deploy pipeline — push timing test ==="
echo "    repo:       $REPO_DIR"
echo "    remote:     $(cd "$REPO_DIR" && git remote get-url origin)"
echo "    iterations: $ITERATIONS  target: <${MAX_PUSH_MS}ms"
echo ""

cleanup() {
    cd "$REPO_DIR"
    if git status --short | grep -q ".pipeline-test-marker"; then
        git rm -f "$MARKER" 2>/dev/null || rm -f "$MARKER"
        git add -A
        git commit -q -m "test: cleanup pipeline test marker"
        git push -q origin main
    elif [ -f "$MARKER" ]; then
        rm -f "$MARKER"
    fi
}
trap cleanup EXIT

for i in $(seq 1 "$ITERATIONS"); do
    cd "$REPO_DIR"
    echo "pipeline-test-iter-$i-$(date +%s)" > "$MARKER"
    git add "$MARKER"
    git commit -q -m "test: pipeline timing iter $i"

    T_START=$(python3 -c "import time; print(time.monotonic())")
    git push -q origin main
    T_END=$(python3 -c "import time; print(time.monotonic())")
    ELAPSED_MS=$(python3 -c "print(int(($T_END - $T_START) * 1000))")

    if [ "$ELAPSED_MS" -lt "$MAX_PUSH_MS" ]; then
        echo "  PASS  iter $i: push ${ELAPSED_MS}ms"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  iter $i: push ${ELAPSED_MS}ms  (limit: ${MAX_PUSH_MS}ms)"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "ALL PASS ($PASS/$ITERATIONS)"
    exit 0
else
    echo "FAILED ($FAIL/$ITERATIONS)"
    exit 1
fi
