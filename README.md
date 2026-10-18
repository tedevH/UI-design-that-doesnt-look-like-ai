# notai — UI design that doesn't look like AI

AI site builders all produce the same page: purple gradient, Inter, a centered hero, three emoji
cards. That isn't a coding problem. Models default to the average of the web, and the average *is*
the vibecoded look.

notai adds the missing piece, **taste**, and keeps it in things you own:

1. **A dataset** of well-designed sites and of vibecoded sites (screenshots and computed styles).
2. **A critic** you train on that dataset. It scores any rendered page from 0 (vibecoded) to 1 (designed).
3. **A stylebook** that clusters good sites into distinct style families, so generation commits to
   one direction instead of averaging all of them.
4. **A generate → render → score → revise loop** driven by the critic and a rule-based tell detector.
5. **A LoRA fine-tune** of a small local coding model on the loop's best pages. The taste ends up in
   weights you run offline.

Everything runs on a 24 GB Apple Silicon Mac at no cost. A Claude API backend is optional.
[PROMPT.md](PROMPT.md) is the full spec the project was built from.

## Setup

```bash
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e '.[all,dev]'
playwright install chromium
ollama pull qwen2.5-coder:7b      # local generator
ollama pull gemma3:4b             # optional: local screenshot critiques
```

## The workflow

### 1. Collect (~600 pages)

```bash
notai scrape --list data/sites/good.txt --source good      # ~130 seed sites; extend to 300+
notai negatives --limit 300                                # lazy-prompt AI pages from data/briefs.txt
notai scrape --list data/sites/vibecoded.txt --source vibe # real vibecoded sites you collect
```

Each page lands in `data/raw/<slug>/` as `desktop.png`, `mobile.png`, `styles.json`, and `meta.json`.
The scraper obeys robots.txt and waits between sites.

### 2. Label

```bash
notai label              # G good · V vibecoded · S skip · U undo
notai label --mode pair  # 1 / 2 / = : which of two is better designed
```

The `--source` you scraped with is a starting guess. Your labels override it. Pair judgments are used
to measure whether the critic ranks pages the way you do.

### 3. Train the critic

```bash
notai critic train
notai critic score runs/<some-run>/r0-c0
```

The critic uses SigLIP embeddings of four crops, plus ~30 measured style features and the tell
count, fed into a logistic regression. It trains in minutes. The report shows cross-validated AUC,
pairwise accuracy, and the "most disputed" pages, which are usually mislabeled.

### 4. Build the stylebook

```bash
notai stylebook --embeddings
notai families
```

This writes `data/stylebook.json` and `data/stylebook.md`. Rename the families and edit their rules
freely. Until you build one, five hand-written families are used (editorial, swiss-tool, brutal-mono,
dark-product, warm-consumer).

### 5. Generate

```bash
notai generate "Booking system for independent climbing gyms"
notai generate "..." --family editorial -n 4 --rounds 3 --vision-model gemma3:4b
notai generate "..." --backend anthropic          # Claude, if you have an API key
notai lint runs/*/best.html                       # tells only, no dependencies
```

Each round renders every candidate and scores it as `critic − 0.04 × tell severity`. The best
candidate is then revised using its specific tells and art-director notes. Every candidate is saved in
`runs/`, and the best one is appended to `data/generations.jsonl`.

### 6. Fine-tune your own model

```bash
notai batch --limit 200                  # run the loop over many briefs
notai dataset build --min-score 0.8      # keep the best page per brief
notai finetune --iters 600               # LoRA on Qwen2.5-Coder-7B (4-bit) with mlx-lm
notai generate "..." --backend mlx --adapter models/adapters/notai
```

Or run the whole chain unattended (generation for N hours, then the top half by score, then the
fine-tune, then a test page), logging to `runs/overnight.log`:

```bash
HOURS=7 caffeinate -i scripts/overnight.sh
```

Repeat: generate with the fine-tuned model, filter with the critic, retrain. A practical way to bootstrap
is to run `batch` with `--backend anthropic` for the first few hundred pages, then switch to your own
model.

## What's verified

- Tests pass (`pytest`). `notai lint` flags 14 tells on a stock AI page and 0 on an editorial page.
- Scraping and style extraction work on live sites (tested on stripe.com and linear.app).
- The critic trains and scores end to end on MPS (SigLIP, transformers 5).
- The full generate loop runs locally with `qwen2.5-coder:7b`, using `gemma3:4b` for critiques.
- Not run here: Claude backend calls and an actual `mlx_lm lora` training run. Their flags and
  parameters were checked against the installed `mlx-lm` and `anthropic` 1.15 packages.

## First real run (Oct 2026, 24 GB M-series Mac, all local)

- Data: 95 sites scraped, 82 kept as good after review (13 dropped for bot walls, cookie walls,
  app screens). 80 lazy-prompt negatives from gemma3:4b, qwen2.5-coder:7b and 14b; 68 kept
  (12 near-blank renders dropped).
- Critic: cross-validated AUC 1.0 on 150 pages, which mostly means real sites and generated pages are
  easy to tell apart. Sanity check on hand-made pages: an editorial page scores 0.53, a stock AI
  landing page 0.20.
- Stylebook: 10 families, mostly light or dark grotesk, plus a mono-technical group and one serif site.
- Generation with qwen2.5-coder:14b: the pages lose the AI clichés but stay bland and
  placeholder-heavy. Best critic scores were 0.28 and 0.006. A 14B base model is the bottleneck;
  this is why the plan bootstraps the fine-tuning data with a stronger model.
- Overnight (7 h, qwen2.5-coder:14b): 52 briefs, median score 0.12, best 0.71. The top-scoring pages
  are mostly monospace + thin borders, so the critic partly rewards a surface style.
- LoRA on Qwen2.5-Coder-7B with the top 26 pages: the first run diverged to NaN (now guarded). The
  retrain was stable (val loss 0.41 → 0.33). On two unseen briefs, mean critic score went from
  0.016 (base 7B) to 0.079 (fine-tuned): more layout ambition (asymmetric grid, large numerals), but
  still placeholder-heavy. Four samples, so treat this as a direction, not a result.

## Studio mode (Gemini)

Small local models can't design on their own, so `notai studio` uses Gemini as the designer and keeps
the rest of the pipeline: your scraped reference screenshots, an art-direction step, generated
photography, rendering, and the tell linter. Each run's cost is measured from the API's token counts.

```bash
notai studio "Natural wine bar in Lisbon with a rotating weekly list"   # cheap: ~$0.20/page
notai studio --limit 20                                                # batch over data/briefs.txt
notai studio "..." --polish                                            # + one judged revision
notai studio "..." --full                                              # 3 candidates on Pro: ~$2/page
```

Cheap mode writes 3 art directions in one call, builds only the strongest with `gemini-3.8-flash`
(low thinking), and generates at most 4 photos with `gemini-3.1-flash-lite-image`. The pages it logs
keep their `data-photo` slots, so `notai dataset build --source gemini-studio` turns them into training
data for the local model.

## Things to know

- **The critic can learn the wrong thing.** If every negative comes from `notai negatives` with one
  model, the critic may learn "looks like Qwen output" rather than "looks vibecoded". Mix in real
  vibecoded sites and negatives from several models, and watch the "most disputed" list.
- **Small vision models give noisy critiques.** `gemma3:4b` sometimes contradicts the style rules.
  Use `--critique-with anthropic` or a larger vision model when quality matters.
- **The tells are heuristics.** Stripe uses a purple gradient and is still well designed. The critic
  is the main signal; tells only nudge the score.
- **Learn patterns, don't copy sites.** Screenshots and styles stay on your machine for training.
  Don't republish them or clone anyone's markup, copy, or assets, and check each site's terms.
- **On 24 GB:** the 7B fine-tune is comfortable. For 14B, close other apps and lower `--max-seq`.
  30B+ needs a rented GPU.
