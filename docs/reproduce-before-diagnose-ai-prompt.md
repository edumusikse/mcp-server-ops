# Bulletproof AI Prompt: Web UI Debugging

Copy this block at the start of any AI debugging session for a web UI issue.
Replace the bracketed parts with your actual details.

---

## Prompt to give the AI

```
I have a UI bug. Before you form any hypothesis or check any code, follow this protocol exactly:

1. Ask me for the exact URL from my browser's address bar if I haven't provided it. 
   Do not construct a URL yourself. I will paste it from my browser, including all 
   query parameters. Do not proceed past this step until you have it.

2. Load that exact URL in your browser tool. Verify you can see the symptom I described.
   If you cannot reproduce the bug, tell me — do not proceed with diagnosis on a working page.

3. Once you can see the symptom, check computed CSS on the non-rendering element first:
   - window.getComputedStyle(el).display
   - window.getComputedStyle(el).height  
   - window.getComputedStyle(el).visibility
   Report what you find before forming any theory.

4. If any CSS value is wrong (display:none, height:0px, visibility:hidden), find the 
   source stylesheet and selector before touching PHP, server code, or JavaScript.

5. Only after CSS is ruled out: check JS, PHP, capabilities, and server state.

Do not skip or reorder these steps. Do not form a hypothesis before step 3.
The bug is often CSS from a third-party plugin, not the code you're thinking about.

---

The bug:
[Describe what you see]

The exact URL from my browser right now:
[Paste URL here]

The element that should show content but doesn't:
[CSS selector or element ID]
```

---

## Why each step is mandatory

**Step 1 — Exact URL**
Query parameters change everything. `?currentTab=x` can cause a plugin to set a `data-attribute` on `<body>` that triggers a CSS rule. Without the parameter, the bug doesn't exist. The AI will test the wrong page for hours.

**Step 2 — Verify reproduction**
If the AI can't see the symptom, all diagnosis is fiction. Require confirmation before allowing any diagnostic work.

**Step 3 — Computed CSS first**
CSS bugs are invisible to PHP and JS tools. A single `display: none` from a third-party stylesheet can make React, PHP, and JS all appear broken when they're fine. Checking CSS takes 30 seconds. Checking everything else takes hours.

**Step 4 — Find the CSS source**
"The element has display:none" is not enough. You need the stylesheet and selector. That tells you which plugin is responsible and how to scope the override.

**Step 5 — Everything else last**
PHP capabilities, JS state, REST API, database values — these are the deep end of the pool. They take time. They are almost never the cause of a "renders but shows nothing" bug. CSS is.

---

## Red flags: stop the AI if you see these

- The AI proposes a hypothesis before showing you the computed CSS
- The AI loads a URL it constructed rather than the one you provided
- The AI says "I can see the element and it looks correct" — ask: with the exact URL you gave it?
- The AI is checking PHP or database values when the element is visually present but empty
- The AI has made 3+ tool calls without reproducing the symptom

If you see any of these, stop the session and say:

> "Stop. Can you reproduce the bug in front of you? Show me the computed height and display of the element using the exact URL I gave you."

---

## The one sentence version

**Give the AI the exact URL and require them to show you the computed CSS on the broken element before they touch anything else.**
