#!/usr/bin/env python3
"""Stop hook: auto-commit all dirty git repos under the ops-agent workspace."""
import json
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/Users/stephan/Documents/ops-agent")


def find_repos(root: Path) -> list[Path]:
    result = subprocess.run(
        ["find", str(root), "-name", ".git", "-type", "d", "-maxdepth", "2"],
        capture_output=True, text=True, timeout=10,
    )
    repos = [Path(line).parent for line in result.stdout.splitlines() if line.strip()]
    repos.sort(key=lambda p: len(p.parts))
    return repos


def has_changes(repo: Path) -> bool:
    r = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True, timeout=10,
    )
    return bool(r.stdout.strip())


def commit_repo(repo: Path, msg: str) -> tuple[bool, str]:
    subprocess.run(["git", "-C", str(repo), "add", "-A"], capture_output=True, timeout=10)
    r = subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", msg],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode == 0:
        first_line = r.stdout.strip().split("\n")[0]
        return True, first_line
    return False, (r.stderr.strip() or r.stdout.strip())[:120]


def main():
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"auto: session end {stamp}"

    repos = find_repos(WORKSPACE)
    committed, failed = [], []

    for repo in repos:
        if not has_changes(repo):
            continue
        ok, detail = commit_repo(repo, msg)
        if ok:
            committed.append(repo.name)
        else:
            failed.append(f"{repo.name} ({detail})")

    parts = []
    if committed:
        parts.append(f"Auto-committed: {', '.join(committed)}")
    if failed:
        parts.append(f"Commit failed: {'; '.join(failed)}")

    if parts:
        print(json.dumps({"systemMessage": " | ".join(parts)}))


if __name__ == "__main__":
    main()
