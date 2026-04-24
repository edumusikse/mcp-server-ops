# Five Hours to Fix One Line: The Most Important Rule for Working with AI

We spent five hours debugging a broken UI. The fix was one line of CSS. Here is what went wrong, and the single rule that prevents it from ever happening again.

---

## What happened

We were editing a course in WordPress. The Rank Math SEO metabox — the panel that shows Focus Keyword, Snippet Preview, and SEO analysis — was showing tab buttons but no content. Empty. Nothing.

We asked Claude to fix it.

Claude spent five hours checking:
- WordPress user capabilities in the database
- PHP filters controlling which metaboxes were visible
- React component state and `window.rankMath.canUser` values
- REST API authentication and nonce validity
- Plugin conflicts and script loading order

Everything checked out. Every PHP value was correct. Every capability was set. The React app was initializing. The DOM had the right elements.

And yet: nothing rendered.

The fix, when we finally found it, was this:

```css
body[data-active-tab] #rank-math-metabox-wrapper .components-panel__body {
  display: block !important;
}
```

One line. Added to our existing CSS override in the mu-plugin.

The cause: LearnDash (the course plugin) has a CSS rule in its own stylesheet that hides all `.components-panel__body` elements whenever a LearnDash tab is active. It does this to clean up its own interface. It accidentally hid every content panel inside Rank Math at the same time.

---

## Why it took five hours

Claude was using a browser automation tool (Playwright) to inspect the page. But it was loading a clean URL:

```
/wp-admin/post.php?post=77405&action=edit
```

The actual URL in our browser was:

```
/wp-admin/post.php?post=77405&action=edit&currentTab=learndash_sfwd-courses_dashboard
```

That `currentTab=learndash_sfwd-courses_dashboard` parameter is set by LearnDash when you navigate between its tabs. It causes LearnDash's JavaScript to set `data-active-tab="learndash_sfwd-courses_dashboard"` on the `<body>` element. That attribute triggers the CSS rule. Without that parameter in the URL, the page loads in a default state, the attribute is never set, and everything works fine.

Claude was debugging a working page. The broken page was never loaded.

Every diagnosis was done on a system that wasn't showing the symptom. All five hours of work were expertise applied to the wrong problem.

---

## The rule

**Reproduce before you diagnose.**

This is not a new idea. Senior engineers refuse to start debugging until they can make the bug appear on demand, in a controlled environment they control, where they can observe it directly.

The reason: you cannot verify a fix for something you cannot reproduce. You cannot trust any diagnosis made on a system that isn't showing the symptom. And you will almost certainly fix the wrong thing.

The rule has one corollary:

**The user's description is not the reproduction case.**

"Rank Math tabs show no content" is a description. It tells you what the user sees. It does not tell you *under what exact conditions* they see it. Those conditions are everything.

The reproduction case is: the exact URL, the exact user session, the exact sequence of clicks that makes the bug appear. Without that, you are guessing.

---

## How to apply it

When something doesn't work in a web UI, the first thing you do — before any diagnosis — is:

1. **Get the exact URL from the browser's address bar.** Not a cleaned-up URL. Not a URL you construct from memory. The one currently in the browser, including every query parameter.

2. **Load that exact URL in your test environment.** Reproduce the bug before you touch anything.

3. **Verify you can see the symptom.** If you cannot see the symptom, you do not have a reproduction case. Stop and find out why.

4. **Only then: start diagnosing.**

When you have a reproduction case, diagnosis is fast. You can check computed CSS. You can read network requests. You can see exactly what the browser sees. What took five hours took two minutes once we had the right URL.

---

## For AI specifically

AI tools are good at forming hypotheses. They are less good at recognizing when their hypothesis-testing environment doesn't match the environment where the bug exists. They will test confidently and thoroughly on the wrong system.

The way to prevent this is to give them the reproduction case before asking them to diagnose. Do not say "Rank Math is broken on course edit pages." Say: "Here is the exact URL. Here is what I see. Make it happen in front of you before you form any theory."

If the AI proposes a diagnosis before loading the exact URL in the exact state you showed it, stop it. The diagnosis is not trustworthy yet.

---

## The one-sentence version

Before you ask anyone — human or AI — to debug something, give them the exact conditions under which the bug appears and verify they can reproduce it.

Everything else follows from that.
