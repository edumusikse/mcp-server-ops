#!/usr/bin/env bash
# One-command workspace health audit.
#
# Runs the full test harness, verifies hook/guard wirings against the repo,
# and reports a single green/red summary. Intended as the answer to the
# question "is this workspace healthy?" — should be runnable locally and in
# CI identically.
#
# Exit 0 = healthy, exit 1 = any failure.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

pass=0
fail=0
fails=()

section() { printf "\n── %s ──\n" "$1"; }
ok()      { printf "  ✓ %s\n" "$1"; pass=$((pass+1)); }
ko()      { printf "  ✗ %s\n" "$1"; fail=$((fail+1)); fails+=("$1"); }

run_test() {
    local name="$1" path="$2"
    if out=$(python3 "$path" 2>&1); then
        ok "$name ($(echo "$out" | tail -1))"
    else
        ko "$name"
        echo "$out" | sed 's/^/      /'
    fi
}

# ─── Unit tests ────────────────────────────────────────────────────────────
section "Unit tests"
run_test "budget_guard"    "tests/test_budget_guard.py"
run_test "payload_guard"   "tests/test_payload_guard.py"
run_test "thrash_guard"    "tests/test_thrash_guard.py"
run_test "runbook_hygiene" "tests/test_runbook_hygiene.py"
run_test "runbook_compliance" "tests/test_runbook_compliance.py"
run_test "runbook_guard"   "tests/test_runbook_guard.py"
run_test "server_imports"  "tests/test_server_imports.py"
run_test "block_ssh"       "tests/test_block_ssh.py"
run_test "workspace_health" "tests/test_workspace_health.py"
run_test "plan_first_guard" "tests/test_plan_first_guard.py"

# ─── Hook wiring (settings.json coherence) ─────────────────────────────────
section "Hook wiring"

settings=".claude/settings.json"
if [[ -f "$settings" ]]; then
    ok "settings.json exists"
    if python3 -c "import json,sys; json.load(open('$settings'))" 2>/dev/null; then
        ok "settings.json is valid JSON"
    else
        ko "settings.json is NOT valid JSON"
    fi
    if grep -q "block-ssh.py" "$settings"; then ok "block-ssh.py referenced"; else ko "block-ssh.py NOT referenced"; fi
    if grep -q "budget_guard.py" "$settings"; then ok "budget_guard.py referenced"; else ko "budget_guard.py NOT referenced"; fi
    if grep -q "runbook_guard.py" "$settings"; then ok "runbook_guard.py referenced"; else ko "runbook_guard.py NOT referenced"; fi
    if grep -q "plan_first_guard.py" "$settings"; then ok "plan_first_guard.py referenced"; else ko "plan_first_guard.py NOT referenced"; fi
else
    ko "settings.json missing"
fi

for h in .claude/hooks/block-ssh.py .claude/hooks/budget_guard.py .claude/hooks/runbook_guard.py .claude/hooks/plan_first_guard.py; do
    [[ -x "$h" ]] && ok "$h executable" || ko "$h not executable"
done

# ─── Guard coherence (every guard has a test) ──────────────────────────────
section "Guard coverage"

# Portable across bash 3.2 (macOS default) and bash 4+ — no associative arrays.
guard_pairs=(
    "thrash_guard|tests/test_thrash_guard.py"
    "payload_similarity_guard|tests/test_payload_guard.py"
    "filter_weak_matches|tests/test_runbook_hygiene.py"
    "flag_runbook_conflicts|tests/test_runbook_hygiene.py"
)
for pair in "${guard_pairs[@]}"; do
    guard="${pair%%|*}"
    test_file="${pair##*|}"
    if grep -q "def $guard" server/guards.py && grep -q "$guard" "$test_file"; then
        ok "$guard → $test_file"
    else
        ko "$guard coverage gap"
    fi
done

# ─── Docs coherence (CLAUDE.md numeric claims match code) ──────────────────
section "Docs coherence"

check_constant() {
    local name="$1" expected="$2" file="$3"
    actual=$(grep -E "^${name}\s*=" "$file" | head -1 | awk -F'=' '{gsub(/[ _]/,"",$2); print $2}' | awk '{print $1}')
    if [[ "$actual" == "$expected" ]]; then
        ok "$name == $expected ($file)"
    else
        ko "$name == $actual, expected $expected ($file)"
    fi
}

check_constant "THRASH_LIMIT"       "5"      "server/guards.py"
check_constant "PAYLOAD_SIM_LIMIT"  "2"      "server/guards.py"
check_constant "DEFAULT_TIME_CAP_MIN" "30"   ".claude/hooks/budget_guard.py"
check_constant "DEFAULT_TOKEN_CAP"  "100000" ".claude/hooks/budget_guard.py"

# CLAUDE.md should reflect the same values
grep -qE "5\+ consecutive"                CLAUDE.md && ok "CLAUDE.md: thrash 5+"               || ko "CLAUDE.md: thrash 5+ missing"
grep -qE "2 distinct tools"               CLAUDE.md && ok "CLAUDE.md: payload 2 tools"         || ko "CLAUDE.md: payload 2 tools missing"
grep -qE "100k output tokens OR 30 min"   CLAUDE.md && ok "CLAUDE.md: budget 100k/30min"       || ko "CLAUDE.md: budget 100k/30min missing"
grep -qE "8KB|8 \* 1024|PAYLOAD_MIN_BYTES" CLAUDE.md && ok "CLAUDE.md: 8KB threshold"          || ko "CLAUDE.md: 8KB threshold missing"

# ─── Runbook mechanism ─────────────────────────────────────────────────────
section "Runbook mechanism"

grep -q "^def lookup_runbook" server/runbook.py && ok "lookup_runbook defined" || ko "lookup_runbook missing"
grep -q "^def read_doc" server/runbook.py && ok "read_doc defined" || ko "read_doc missing"
grep -q "^def record_runbook_outcome" server/runbook.py && ok "record_runbook_outcome defined" || ko "record_runbook_outcome missing"

[[ -f "tests/runbook_compliance.py" ]] && ok "runbook_compliance analyzer present" || ko "runbook_compliance missing"
[[ -f "tests/self_audit.py" ]]         && ok "self_audit drift detector present"    || ko "self_audit missing"

# ─── Local/deploy parity (static only — run --live by hand) ────────────────
section "Local/deploy parity"
if out=$(python3 tests/live_ops_parity.py 2>&1); then
    ok "live_ops_parity static checks"
else
    ko "live_ops_parity static checks"
    echo "$out" | sed 's/^/      /'
fi

# ─── Summary ───────────────────────────────────────────────────────────────
section "Summary"
total=$((pass + fail))
printf "  %d/%d checks passed\n" "$pass" "$total"
if (( fail > 0 )); then
    printf "\nFailures:\n"
    for f in "${fails[@]}"; do printf "  - %s\n" "$f"; done
    exit 1
fi
printf "\nWorkspace healthy.\n"
exit 0
