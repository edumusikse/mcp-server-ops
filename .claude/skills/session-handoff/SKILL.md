---
name: session-handoff
description: Produce a structured handoff so the next session can resume without losing context. Writes .claude/handoffs/LATEST.md (auto-injected by SessionStart hook) + a timestamped archive. Use when Stephan says "/session-handoff", "wrap up", "handoff", "save state", "we're done for today", or when context is nearing 60% and work is mid-stream.
---

# Session handoff

Stephan has been burned by summaries that were written but never read. This
skill closes that loop: the output is written to a path the SessionStart
hook [session_handoff_inject.py](.claude/hooks/session_handoff_inject.py)
reads automatically, so the next session cannot miss it.

## What to produce

Write a handoff with EXACTLY these sections, in this order. Keep the whole
file under 200 lines / ~2.5k tokens — this gets re-injected every
new session, so bloat compounds.

```markdown
# Session handoff — {YYYY-MM-DD HH:MM}

## Shipped this session
- <one-line summary> — [file](path#Lline) or commit `<shorthash>`
- ...

## In-flight (paused mid-task)
- **Task:** <what was being built>
- **State:** <what's done vs. what's not, concretely>
- **Next step:** <single unambiguous action — the first thing to do next session>
- **Blocker, if any:** <what's stopping it>

## Decisions made + WHY
- <decision> — because <reason>. Alternative <X> was rejected because <Y>.
- ...

## Key files touched
- [path](path) — what changed and why
- ...

## Open questions / deferred
- <question Stephan needs to answer OR thing explicitly deferred>
- ...

## Next action (single line)
<The one thing the next session should do first. No menu, no options.>
```

## Rules

1. **Facts only.** Every claim points at a file, line range, commit, or
   tool-call result. No vague "improved X" — "added payload_guard check to
   read_file at [server/files.py:42-58]".
2. **Drop the noise.** Exploratory dead-ends that didn't ship don't belong
   unless they're load-bearing for a future decision (then move them to
   "Decisions made + WHY").
3. **Next action is one line.** If you can't reduce it to one line, the
   session isn't actually handoff-ready — name the blocker in
   "In-flight" and put "decide <X>" as the next action.
4. **Preserve the WHY.** Decisions without rationale rot fastest. If the
   next session can't tell why a path was chosen, it will re-open the
   debate and burn tokens.

## Where to write it

Two files, atomically (write archive first, then LATEST so a crash mid-write
never leaves LATEST stale):

1. `.claude/handoffs/{YYYY-MM-DD-HHMM}.md` — archive, immutable history.
2. `.claude/handoffs/LATEST.md` — overwritten each run. This is the file
   the SessionStart hook reads.

Create the `.claude/handoffs/` directory if missing.

Use the `Write` tool for both. Do NOT commit these files — they're local
session state, add `.claude/handoffs/` to `.gitignore` the first time this
skill runs if the entry isn't already there.

## After writing

Print a ≤3-line confirmation:
- Path to LATEST.md
- Token count (rough: `wc -w` on the file, multiply by 1.3)
- Next action, echoed

Do not re-summarize the handoff in prose — Stephan can read the file.
