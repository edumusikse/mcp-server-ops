# Technical Post-Mortem: Rank Math UI Failure — Root Cause and Diagnostic Protocol

## Timeline

- **5 hours** of active debugging
- **1 line** of CSS to fix
- **Root cause found**: 2 minutes after loading the correct URL

---

## The bug

On KSM (kita-seminar-manufaktur.de), the Rank Math SEO metabox on `sfwd-courses` (LearnDash) edit screens showed tab buttons (Allgemein, Erweitert, Schema, Sozial) but no content in any tab panel. The panels were in the DOM, React had initialized, all capabilities were correctly set.

**Actual cause:**

LearnDash's `dist/header.min.css?ver=5.0.5` contains:

```css
body[data-active-tab]:not([data-active-tab="post-body-content"]) .components-panel__body {
  display: none;
}
```

LearnDash's JavaScript sets `data-active-tab` on `<body>` whenever a LearnDash tab is active. On the course edit page, navigating through LearnDash tabs sets this attribute to values like `learndash_sfwd-courses_dashboard`. Since this is never `"post-body-content"`, the rule fires and hides every `.components-panel__body` on the page — including all of Rank Math's section panels (SERP preview, Focus Keyword, SEO checklist).

**Why it was invisible in testing:**

All Playwright sessions loaded:
```
/wp-admin/post.php?post=77405&action=edit
```

The actual browser URL was:
```
/wp-admin/post.php?post=77405&action=edit&currentTab=learndash_sfwd-courses_dashboard
```

Without `currentTab`, LearnDash's JS never sets `data-active-tab` on page load. The CSS rule never fires. The page works correctly. Five hours of diagnosis was performed on a working page.

---

## What was checked (and was correct)

- `wp_user_roles` → `rank_math_onpage_*` all `true` for administrator role ✓
- `window.rankMath.canUser` → all fields `true` ✓
- `window.rankMath.currentEditor` → `"classic"` ✓
- `rank_math_metabox` DOM presence → found, `display: block` ✓
- `#rank-math-metabox-wrapper` child count → 1 (React rendered) ✓
- `rank-math-app.js` loading → confirmed ✓
- Perfmatters script manager → empty, no blocks ✓
- `get_user_option_metaboxhidden_sfwd-courses` → `rank_math_metabox` not hidden ✓
- JS console errors → none from Rank Math ✓

All of these were correct. None of them were the problem.

---

## How to diagnose this in 2 minutes

```javascript
// Step 1: check computed height on the panel
window.getComputedStyle(document.getElementById('0-general-view')).height
// → "0px" (broken) or "784px" (working)

// Step 2: check body attribute
document.body.getAttribute('data-active-tab')
// → "learndash_sfwd-courses_dashboard" (broken state)

// Step 3: find the CSS rule
for (const sheet of document.styleSheets) {
  try {
    for (const rule of sheet.cssRules || []) {
      if (rule.selectorText?.includes('components-panel__body') 
          && rule.style?.display === 'none') {
        console.log(rule.selectorText, sheet.href);
      }
    }
  } catch(e) {}
}
// → prints the LearnDash rule and header.min.css
```

Total time with exact URL loaded: under 2 minutes.

---

## The fix

In `10-classic-editor.php`, added to the existing `admin_head` CSS injection on `sfwd-courses` screens:

```css
body[data-active-tab] #rank-math-metabox-wrapper .components-panel__body {
  display: block !important;
}
```

Scoped to `#rank-math-metabox-wrapper` to avoid interfering with LearnDash's legitimate use of the rule on its own UI.

---

## Systemic failure: diagnosis without reproduction

The diagnostic protocol failed at step zero: **no reproduction case was established**.

The correct protocol for any UI bug where an element renders but shows no content:

### Step 1 — Get the exact URL
Ask the user for their browser's address bar URL. Do not construct a URL. Copy theirs exactly, including all query parameters. Query parameters change which CSS and JS execute.

### Step 2 — Reproduce in test environment
Load that exact URL. Verify the symptom is visible. If you cannot see the symptom, you do not have a reproduction case — stop and find out why before proceeding.

### Step 3 — Check computed CSS first
```javascript
const el = document.querySelector('#target-element');
console.log(
  window.getComputedStyle(el).display,
  window.getComputedStyle(el).height,
  window.getComputedStyle(el).visibility
);
```
If any of these are wrong (`none`, `0px`, `hidden`), find the CSS source before touching PHP or JS.

### Step 4 — Find the CSS source
```javascript
for (const sheet of document.styleSheets) {
  try {
    for (const rule of sheet.cssRules || []) {
      if (!rule.selectorText || !rule.style?.display) continue;
      if (rule.style.display === 'none' || rule.style.height === '0px') {
        // Check if this rule could match your element
        try {
          if (document.querySelector(rule.selectorText)) {
            console.log(rule.selectorText, '->', rule.style.cssText, sheet.href);
          }
        } catch(e) {}
      }
    }
  } catch(e) {}
}
```

### Step 5 — Only then: check PHP, capabilities, and JS

PHP and JS should be checked only after CSS is ruled out. CSS bugs are invisible to PHP/JS diagnostic tools and are found in under 2 minutes once you're looking in the right place.

---

## Lesson for third-party plugin interaction

When two plugins both use WordPress's admin interface, CSS class name collisions are common. `.components-panel__body` is a WordPress core component class. LearnDash chose to use it in a CSS selector that hides elements globally. Any plugin that uses that class (Rank Math, Gutenberg blocks, others) is silently affected.

When debugging any plugin that works on some post types but not others, or works on clean URLs but not after navigation, check for broad CSS selectors from other plugins targeting shared class names.

---

## Summary

| What we checked | Time spent | Was it the problem? |
|---|---|---|
| PHP capabilities, user meta | ~2 hours | No |
| React state, canUser, JS errors | ~1.5 hours | No |
| DOM structure, metabox visibility | ~1 hour | No |
| Computed CSS on panel element (exact URL) | 2 minutes | **Yes** |

The fix was always 2 minutes away. The URL was the key.
