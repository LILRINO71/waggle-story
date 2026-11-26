# What Is Waggle?

An animated walk-through of [Waggle](https://github.com/LILRINO71/waggle), a personal AI assistant that runs on one
PC: what it is, why it is being built, how a message travels through it, the tools it is made of, and what the
Claude usage would have cost at API prices.

**Open it:** https://lilrino71.github.io/waggle-story/

Scroll, or use the arrow keys to move scene by scene. "Present" goes full screen; "Motion on/off" stops the animation.

## Files

- `index.html`: the page source (content only, no `<html>` shell).
- `build.py`: wraps it into `docs/index.html` (served by GitHub Pages) and `Waggle Story.html` (opens by double-click).

```
python build.py
```

## Where the numbers come from

Everything on the page is taken from Waggle's own repository (`README.md`, `docs/STATUS.md`, git history) and its
runtime records. The API-price figure is an estimate: token counts from saved Claude Code session logs, priced at
Anthropic's list API rates in November 2026. The work itself ran on a flat-rate subscription.
