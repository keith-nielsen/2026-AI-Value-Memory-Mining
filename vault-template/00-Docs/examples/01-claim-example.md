---
captured: 2026-05-28
---
# Claim: figure out git bisect

Burned ~3 hours today hunting the commit that broke the nightly build. Checked out
commits more or less at random and rebuilt each time. Painful and slow.

A colleague mentioned `git bisect` does this "automatically" with binary search —
sounds like it could have turned 3 hours into 20 minutes. Worth a proper look; it
could change how I handle every regression from here on.

Tags:: #technology #debugging #git

<!--
  This is a CLAIM — a raw capture in 20-Claims/. Claims are deliberately
  unstructured: no rigid schema, no grade, no commitment yet. The only discipline
  at this stage is capturing the thought before it evaporates. Everything else
  (is it worth digging? how valuable?) is decided later, at Prospect and Sort.
-->
