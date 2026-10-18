"""The critic: scores how well-designed (vs. vibecoded) a rendered page looks.

Features = SigLIP embeddings of four crops + handcrafted style features + tell count,
fed to a logistic regression. Small enough to train in minutes on a laptop.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from . import config, tells, tokens
from .config import need


# ---------- image embeddings ----------

@lru_cache(maxsize=2)
def _embedder(model_name: str):
    torch = need("torch", "critic")
    transformers = need("transformers", "critic")
    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    model = transformers.AutoModel.from_pretrained(model_name).to(device).eval()
    processor = transformers.AutoImageProcessor.from_pretrained(model_name)  # images only: no tokenizer deps
    return model, processor, device


def crops(desktop: Path, mobile: Path | None):
    """Desktop above-the-fold, two lower desktop bands, mobile fold. Squares, so detail survives resize."""
    Image = need("PIL.Image", "critic")
    img = Image.open(desktop).convert("RGB")
    w, h = img.size
    fold = img.crop((0, 0, w, min(h, int(w * 0.625))))
    bands = []
    for frac in (0.35, 0.7):
        top = int(max(0, h * frac - w * 0.3))
        bands.append(img.crop((0, top, w, min(h, top + int(w * 0.6)))))
    out = [fold] + bands
    if mobile and Path(mobile).exists():
        m = Image.open(mobile).convert("RGB")
        out.append(m.crop((0, 0, m.width, min(m.height, int(m.width * 1.6)))))
    else:
        out.append(fold)
    return out


def embed_images(images, model_name: str = config.DEFAULT_EMBED_MODEL):
    torch = need("torch", "critic")
    np = need("numpy", "critic")
    model, processor, device = _embedder(model_name)
    with torch.no_grad():
        inputs = processor(images=images, return_tensors="pt").to(device)
        feats = model.get_image_features(**inputs)
        if not torch.is_tensor(feats):  # transformers >= 5 returns a model output object
            feats = feats.pooler_output
        feats = feats / feats.norm(dim=-1, keepdim=True)
    return feats.float().cpu().numpy().astype(np.float32)


def page_embedding(desktop: Path, mobile: Path | None, model_name: str = config.DEFAULT_EMBED_MODEL, cache_key: str | None = None):
    """[fold embedding, mean(other crops)] — cached on disk per (model, cache_key)."""
    np = need("numpy", "critic")
    cache = None
    if cache_key:
        cache = config.CACHE / "emb" / model_name.replace("/", "__") / f"{cache_key}.npy"
        if cache.exists() and cache.stat().st_mtime >= Path(desktop).stat().st_mtime:
            return np.load(cache)
    e = embed_images(crops(Path(desktop), mobile), model_name)
    vec = np.concatenate([e[0], e[1:].mean(axis=0)])
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        np.save(cache, vec)
    return vec


def style_vector(styles: dict | None):
    np = need("numpy", "critic")
    styles = styles or {}
    v = tokens.vector(styles) + [float(tells.penalty(tells.from_styles(styles)))]
    return np.array(v, dtype=np.float32)


def page_features(d: Path, model_name: str, cache_key: str | None = None):
    np = need("numpy", "critic")
    styles_path = d / "styles.json"
    styles = json.loads(styles_path.read_text()) if styles_path.exists() else {}
    emb = page_embedding(d / "desktop.png", d / "mobile.png", model_name, cache_key)
    return np.concatenate([emb, style_vector(styles)])


# ---------- training ----------

def train(model_name: str = config.DEFAULT_EMBED_MODEL, out: Path = config.CRITIC, C: float = 0.5) -> dict:
    np = need("numpy", "critic")
    joblib = need("joblib", "critic")
    sk_lm = need("sklearn.linear_model", "critic")
    sk_pipe = need("sklearn.pipeline", "critic")
    sk_pre = need("sklearn.preprocessing", "critic")
    sk_ms = need("sklearn.model_selection", "critic")
    from .label import pair_labels, resolved_labels

    labels = resolved_labels()
    n_good = sum(labels.values())
    n_bad = len(labels) - n_good
    if n_good < 10 or n_bad < 10:
        raise SystemExit(f"Need at least 10 good and 10 vibecoded pages to train (have {n_good} / {n_bad}).")

    slugs = sorted(labels)
    print(f"embedding {len(slugs)} pages with {model_name} (cached after the first run)...")
    X, keep = [], []
    for i, slug in enumerate(slugs, 1):
        try:
            X.append(page_features(config.RAW / slug, model_name, cache_key=slug))
            keep.append(slug)
        except Exception as e:
            print(f"  skip {slug}: {e}")
        if i % 50 == 0:
            print(f"  {i}/{len(slugs)}")
    if len(keep) < 20:
        raise SystemExit(f"Only {len(keep)} pages could be embedded; see the errors above.")
    X = np.stack(X)
    y = np.array([labels[s] for s in keep])

    def make():
        return sk_pipe.make_pipeline(
            sk_pre.StandardScaler(),
            sk_lm.LogisticRegression(C=C, class_weight="balanced", max_iter=5000),
        )

    folds = max(2, min(5, int(min(y.sum(), len(y) - y.sum()))))
    cv = sk_ms.StratifiedKFold(n_splits=folds, shuffle=True, random_state=0)
    probs = sk_ms.cross_val_predict(make(), X, y, cv=cv, method="predict_proba")[:, 1]
    from sklearn.metrics import accuracy_score, roc_auc_score

    report = {
        "n": int(len(y)), "good": int(y.sum()), "vibe": int(len(y) - y.sum()),
        "cv_auc": round(float(roc_auc_score(y, probs)), 4),
        "cv_accuracy": round(float(accuracy_score(y, probs > 0.5)), 4),
        "embed_model": model_name,
    }

    # Pairwise agreement: does the cross-validated score order human pairs correctly?
    p_of = dict(zip(keep, probs))
    pairs = [(a, b, p) for a, b, p in pair_labels() if a in p_of and b in p_of and p != 0.5]
    if pairs:
        agree = sum((p_of[a] > p_of[b]) == (p > 0.5) for a, b, p in pairs)
        report["pairwise_accuracy"] = round(agree / len(pairs), 4)
        report["pairs"] = len(pairs)

    model = make().fit(X, y)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "embed_model": model_name, "report": report,
                 "feature_names": ["emb"] * (X.shape[1] - len(tokens.FEATURE_NAMES) - 1) + tokens.FEATURE_NAMES + ["tell_penalty"]}, out)

    # Show the pages the critic disagrees with most: often mislabeled, worth a second look.
    worst = sorted(zip(keep, y, probs), key=lambda t: -abs(t[1] - t[2]))[:10]
    report["most_disputed"] = [{"slug": s, "label": int(l), "score": round(float(p), 3)} for s, l, p in worst]
    return report


# ---------- scoring ----------

class Critic:
    def __init__(self, path: Path = config.CRITIC):
        if not Path(path).exists():
            raise SystemExit(f"No critic at {path}. Train one with `notai critic train`.")
        joblib = need("joblib", "critic")
        bundle = joblib.load(path)
        self.model = bundle["model"]
        self.embed_model = bundle["embed_model"]
        self.report = bundle.get("report", {})

    def score_dir(self, d: Path) -> float:
        x = page_features(Path(d), self.embed_model)
        return float(self.model.predict_proba(x[None, :])[0, 1])


def try_load(path: Path = config.CRITIC) -> Critic | None:
    """The critic if one has been trained, else None (generation falls back to tells only)."""
    return Critic(path) if Path(path).exists() else None
