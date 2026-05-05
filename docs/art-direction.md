# Art Direction

## Style: Cosmic Nouveau

A fusion of Alphonse Mucha's art nouveau composition with Jean Giraud (Moebius)'s surreal sci-fi linework. Medieval subjects rendered as if glimpsed through the eyes of a civilization that touched something infinite. Not dark fantasy — luminous strangeness.

## Core Principles

- **Mucha's composition, Moebius's world.** Elegant, flowing arrangements housing vast and impossible landscapes. Ornamental flourishes frame scenes that stretch toward alien horizons.
- **Clean linework.** Precise, confident lines with subtle crosshatching for depth. No grit, no splatter, no rough edges. Every line is deliberate.
- **Muted earthy palette with subtle accents.** Dusty ochres, warm stones, faded sage, parchment cream. Color accents are restrained — a wash of copper, a thread of deep teal, a distant violet sky. Never saturated. Never loud.
- **Figures are grounded, tasteful, elegant, and curvy.** People have weight and presence. They stand with quiet confidence, not heroic poses. Bodies are natural and graceful — Moebius's groundedness with Mucha's flowing curves. Clothing drapes and moves.
- **Vast landscapes, subtle flourishes.** Art breathes. Scenes open into endless deserts, impossible architecture, skies with too many moons. Decorative elements are woven into the scene itself — a vine curling around a column, a geometric pattern in the stonework — not stamped on as borders. The app handles card frames.
- **No borders in the art.** Card art is full-bleed imagery. Frames, borders, and card chrome are handled by the application UI.

## Mood

**Dreamy. Cosmic. Vast. Strange.**

These cards feel like fragments of a half-remembered vision. A market scene where the stalls stretch into infinity. A chapel whose ceiling opens to a sky full of rings. A smithy built into the ribcage of something ancient and colossal. The world is familiar — villages, castles, chapels — but the scale is wrong, the geometry is soft, and the light comes from somewhere you can't quite identify.

## What to Avoid

- Grimdark, gore, decay, horror
- Hard sci-fi elements (spaceships, guns, screens)
- Bright saturated colors or neon
- Chibi, cartoon, or stylized proportions
- Photorealism
- Busy, cluttered compositions
- Heavy black outlines or comic-book inking
- Ornamental borders or frames within the art itself

## Prompting Guide

### Model Recommendation

**Flux** handles Moebius-style linework best out-of-the-box. Midjourney v7 is a strong alternative with better consistency tools (`--sref` style references). Either works — pick one and stay on it for the full set.

### Prompt Structure

Prompts use comma-separated phrases (not sentences), ordered:

```
[Subject/scene], [composition/framing], [style suffix]
```

- **4-6 descriptive phrases** for the subject/scene. Be specific and visual — "a woman in draped linen standing before a stone archway" not "a person near a building."
- **Strong silhouette, clear focal point.** Card art reads at small scale. Shape > detail.
- **Simple or vast backgrounds.** Never busy. A gradient, a desert horizon, a single sky — let the subject breathe.
- **No filler words.** Never use "masterpiece," "highly detailed," "best quality," "beautiful." Modern models ignore these.
- **Lock terminology.** Use the exact same style words across every prompt. Never swap synonyms (e.g. don't alternate between "ink linework" and "pen illustration").

### Negative Prompt (for SD/Flux)

Include with every generation:

```
blurry, distorted, extra limbs, watermark, signature, text, border, frame,
low resolution, photorealistic, neon colors, grimdark, gore, cartoon,
chibi, comic book inking, busy background
```

### Style Suffix

Append this **verbatim** to every card prompt. Do not modify it per-card:

```
art nouveau composition (Alphonse Mucha) fused with surreal linework
(Jean Giraud / Moebius), clean precise lines, subtle crosshatching,
muted earthy palette — ochre stone sage cream — with restrained color
accents, grounded elegant curvy figures, vast dreamlike landscape,
impossible architecture, soft geometry, subtle decorative flourishes
woven into scene, dreamy cosmic mood, full bleed illustration,
no text, no border, no frame, no watermark
```

### Consistency Across the Set

- **Batch by category.** Generate all Treasure cards together, then Victory, then Kingdom actions. This reduces style drift.
- **One model, one checkpoint.** Don't switch models mid-set.
- **Post-process uniformly.** Apply the same color grading / level adjustment to every output to smooth variance.
- **Aspect ratio:** Portrait 2:3 (e.g. 768x1152 or 1024x1536). Generate large, downscale for the app.

### Per-Card Prompt Template

```
[Scene description — 4-6 specific visual phrases], [composition note],
[style suffix]
```

Example (Village card):
```
A cluster of sandstone dwellings nestled at the base of an immense
spiraling mesa, warm light spilling from arched doorways, figures in
draped linen carrying water vessels along a winding path, distant sky
with two pale moons, centered composition with strong vertical
silhouette, art nouveau composition (Alphonse Mucha) fused with surreal
linework (Jean Giraud / Moebius), clean precise lines, subtle
crosshatching, muted earthy palette — ochre stone sage cream — with
restrained color accents, grounded elegant curvy figures, vast dreamlike
landscape, impossible architecture, soft geometry, subtle decorative
flourishes woven into scene, dreamy cosmic mood, full bleed
illustration, no text, no border, no frame, no watermark
```
