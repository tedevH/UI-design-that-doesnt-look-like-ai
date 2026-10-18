# Master build prompt

This is the full spec this repo was built from. You can hand it to any coding
agent to rebuild or extend the project. Everything in `notai/` implements it.

---

## Role

You are building **notai**: a local-first system that generates web UI that does
not look AI-generated ("vibecoded"). It runs on a single Apple Silicon Mac with
24 GB of unified memory. No paid service is required; an API model is optional.

## The core idea

Code-writing models already write good HTML/CSS. What they lack is **taste**:
left alone they pick the statistical average of every website, and that
average *is* the vibecoded look. So the system is not "a model that writes UI".
It is:

1. a **dataset** of well-designed sites and of vibecoded sites,
2. a **critic** that learns the difference and scores any rendered page,
3. a **stylebook** that turns good sites into concrete, distinct style families
   (so generation commits to one direction instead of averaging),
4. a **generate → render → score → revise loop** driven by the critic,
5. a **fine-tune** of a small open coding model on the loop's best outputs, so
   the taste ends up in weights you own and can run offline.

Never average across families. Never clone a real site's markup, copy, or
assets: learn measurable rules (type scale, palette size, spacing rhythm,
radius, density, layout structure), not pages.

## What "vibecoded" means (the tells)

Detect and penalize these, both in generated HTML source and in rendered
computed styles:

- Purple/violet/indigo-to-blue or pink gradients, especially on hero text or buttons
- Gradient text (`background-clip: text`) on headlines
- Inter / system-ui as the only typeface, with no typographic contrast
- Large uniform corner radius on everything (`rounded-2xl`, `rounded-3xl`, 16–24px+)
- Glassmorphism: `backdrop-filter: blur` panels, translucent white cards
- Centered hero → three identical icon cards → testimonials → CTA band → footer
- Emoji or generic icon-in-a-circle used as feature icons
- Soft drop shadows on every card; glow effects
- Every section the same height, spacing and alignment (no rhythm)
- Tailwind default palette values used unmodified (indigo-500, slate-900, etc.)
- Marketing clichés: "Unlock", "Supercharge", "Elevate", "Seamless",
  "Revolutionize", "Next-generation", "Empower", "Effortlessly",
  "Get started today", "Trusted by thousands", "All-in-one platform"
- Placeholder content: "Lorem ipsum", "John Doe", "Acme", fake round stats
  ("10,000+ users", "99.9% uptime") with no context
- Dark mode by default with neon accent and grid/noise background

## What good sites tend to do instead

- One strong typographic idea: a distinctive display face or a deliberate
  serif/sans pairing, a steep type scale (largest/body ≥ 3.5), tight display
  tracking, measured line lengths (55–75ch)
- A small palette: 1–2 neutrals that are slightly warm or cool (never pure
  #000/#fff everywhere), one accent used sparingly
- Spacing rhythm with contrast: dense where information lives, generous
  around moments; not one gap value repeated everywhere
- Layout asymmetry and real grids: left-aligned heroes, uneven columns,
  content that breaks the grid on purpose
- Specific, concrete copy that names the product, the user and the outcome
- Real artifacts: product screenshots, real photography, real numbers with
  units and sources — or deliberately none
- Small radii (0–8px) or one consistent radius, borders over shadows

## Hardware and model constraints (24 GB Mac)

- Critic: SigLIP image embeddings (`google/siglip-base-patch16-224` default)
  plus handcrafted style features, logistic regression. Runs on MPS/CPU.
- Generator (local): a ~7B coding model, 4-bit, via Ollama or MLX. Fine-tune
  with LoRA in MLX (`mlx-lm`). 14B is possible but tight; 30B+ is not.
- Generator (optional API): Claude via the official `anthropic` SDK,
  model `claude-opus-5-5`, streaming, adaptive thinking.
- Every heavy dependency is imported lazily so `notai lint` and the tests run
  with only the standard library.

## Components to build

### 1. `notai scrape` — collection
- Input: a text file of URLs/domains (`#` comments allowed) and a `--source`
  prior (`good` or `vibe`).
- Playwright Chromium. For each site: obey `robots.txt`, identify with a
  descriptive user agent, wait between requests.
- Save to `data/raw/<slug>/`: `desktop.png` (1440 wide, full page capped at
  ~6000px), `mobile.png` (390 wide), `styles.json` (output of
  `notai/assets/extract.js`), `meta.json` (url, title, source, timestamp).
- Dismiss nothing that needs consent; just screenshot what loads.

### 2. `extract.js` — computed style extraction (runs in the page)
Sample visible elements and aggregate: font families weighted by text length,
font sizes, weights, line heights, letter spacing, text and background
colors weighted by area, gradients, border radii, box shadows,
backdrop-filters, padding/margin/gap values, emoji count, headings with their
sizes and alignment, and top-level section boxes with the number of
same-row children (to detect "3 identical cards" rows).

### 3. `notai/tokens.py` — features
Turn `styles.json` into a flat numeric feature dict: type scale ratio,
number of font families/sizes, palette size, neutral temperature, accent
saturation, gradient and purple-gradient flags, median radius, share of large
radii, shadow share, blur count, spacing-grid adherence, emoji count, number
of equal-card rows, centered hero flag.

### 4. `notai/tells.py` — the vibecoded detector
Rule-based. Works on raw HTML/CSS text alone, optionally enriched with
`styles.json` features. Returns a list of `Tell(name, severity 1–3,
evidence)`. Also exposed as `notai lint file.html` with zero dependencies.

### 5. `notai label` — labeling tool
A local web app (standard library `http.server` + one HTML page). Two modes:
- **single**: one screenshot; keys `G` good, `V` vibecoded, `S` skip, `U` undo
- **pair**: two screenshots; keys `1`/`2` better, `=` tie
Writes append-only `data/labels.jsonl`. Human labels override the source
prior.

### 6. `notai negatives` — synthetic vibecoded pages
Prompt a generator with the typical lazy request ("Build a modern landing
page for {brief}, single HTML file, Tailwind CDN") for each line of
`data/briefs.txt`, render, and save as `source=vibe`. This is the cheapest
way to get hundreds of archetypal negatives.

### 7. `notai critic train|score`
- Embed 4 crops per site (desktop fold, two lower desktop crops, mobile fold)
  with SigLIP; cache embeddings in `data/cache/`.
- Features = [fold embedding, mean of other crops, style features, tell count].
- `StandardScaler` + `LogisticRegression(class_weight="balanced")`.
- Report 5-fold ROC-AUC and, if pair labels exist, pairwise accuracy.
- Save `models/critic.joblib`. `score` returns P(good) for screenshots.

### 8. `notai stylebook build`
Cluster the good sites (style features + embeddings when available) with
k-means into 8–16 families. For each family write concrete rules: font
stacks seen, type scale, palette swatches, radius, shadow/border usage,
density, alignment, plus 3 example slugs. Auto-name families from their
traits; names are editable in `data/stylebook.json`.

### 9. `notai generate "<brief>"`
- Choose a family (`--family` or auto: ask the generator to pick from the
  family list given the brief).
- System prompt = the house rules + family rules + the anti-tells list.
- Produce N candidates per round with different layout directives.
- Render each with Playwright, run tells and the critic, compute
  `score = P(good) − 0.04 × Σ severity`.
- Revise the best candidate with the concrete tells and critic score as
  feedback. Stop at `--target` or after `--rounds`.
- Save every candidate to `runs/<timestamp>-<slug>/` and append the best to
  `data/generations.jsonl`.

### 10. `notai dataset build`
From `data/generations.jsonl`, keep the top candidate per brief above
`--min-score`, and write chat-format JSONL (`system`, `user`, `assistant`) to
`data/sft/train.jsonl` and `valid.jsonl` (90/10). Use the compact system
prompt so the fine-tuned model learns the style instead of reading it.

### 11. `notai finetune`
Wrap `mlx_lm lora` (LoRA, gradient checkpointing, batch size 1, prompt
masking) on `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit` by default, then
optionally `mlx_lm fuse`. Then `notai generate --backend mlx --adapter ...`
uses the result, and the loop repeats: generate → filter → retrain.

## Success criteria

- `notai lint` flags a stock AI landing page with ≥ 5 tells and a clean
  editorial page with ≤ 1.
- Critic cross-validated AUC ≥ 0.85 on ≥ 300 + 300 labeled pages.
- In a blind test, designers can't reliably pick generated pages out of a
  mix with real good sites.

## Rules for the agent building this

- Python ≥ 3.11, one package `notai`, one CLI entry point, argparse only.
- Lazy-import heavy dependencies inside the functions that need them, with a
  clear install hint on `ImportError`.
- All paths relative to the project root (override with `NOTAI_HOME`).
- Append-only JSONL for labels and generations. Never delete user data.
- Tests for the pure-Python parts (tells, tokens, prompts, stylebook naming).
