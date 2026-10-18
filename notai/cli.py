"""notai command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config


def _backend_args(p: argparse.ArgumentParser, default: str = "ollama") -> None:
    p.add_argument("--backend", default=default, choices=["ollama", "mlx", "anthropic"])
    p.add_argument("--model", help="model name for the backend (defaults per backend)")
    p.add_argument("--adapter", help="LoRA adapter path (mlx backend)")
    p.add_argument("--vision-model", help="Ollama vision model for critiques, e.g. qwen2.5vl:7b")


def _backend(a):
    from .backends import make

    return make(a.backend, a.model, a.adapter, getattr(a, "vision_model", None))


def cmd_scrape(a):
    from .scrape import scrape

    scrape(Path(a.list), a.source, limit=a.limit, delay=a.delay, force=a.force, mobile=not a.no_mobile)


def cmd_negatives(a):
    from .generate import negatives
    from .util import read_list

    negatives(_backend(a), read_list(Path(a.briefs)), limit=a.limit)


def cmd_label(a):
    from .label import serve

    serve(a.mode, a.port)


def cmd_critic(a):
    if a.action == "train":
        from .critic import train

        report = train(a.embed_model, C=a.C)
        print(json.dumps(report, indent=2))
        return
    from .critic import Critic

    critic = Critic()
    if a.action == "info":
        print(json.dumps(critic.report, indent=2))
        return
    for path in a.paths:
        d = Path(path)
        d = d if d.is_dir() else d.parent
        print(f"{critic.score_dir(d):.3f}  {d}")


def cmd_stylebook(a):
    from .stylebook import build

    book = build(k=a.k, use_embeddings=a.embeddings)
    for f in book["families"]:
        print(f"{f['id']}  {f['size']:>3} sites  {f['name']}   e.g. {', '.join(f['examples'][:3])}")
    print(f"wrote {config.STYLEBOOK} and {config.STYLEBOOK.with_suffix('.md')}")


def cmd_families(a):
    from .generate import families

    for f in families():
        print(f"{f['id']:<14} {f.get('name', '')}")


def cmd_generate(a):
    from .generate import run

    backend = _backend(a)
    critic_backend = None
    if a.critique_with:
        from .backends import make

        critic_backend = make(a.critique_with)
    run(a.brief, backend, family=a.family, n=a.n, rounds=a.rounds, target=a.target,
        vision=bool(a.vision_model or a.critique_with), critic_backend=critic_backend)


def cmd_batch(a):
    from .generate import run
    from .util import read_list

    backend = _backend(a)
    briefs = read_list(Path(a.briefs))[: a.limit]
    for i, brief in enumerate(briefs, 1):
        print(f"\n=== [{i}/{len(briefs)}] {brief}")
        try:
            run(brief, backend, family=a.family, n=a.n, rounds=a.rounds, target=a.target, vision=bool(a.vision_model))
        except Exception as e:  # keep the batch going
            print(f"failed: {e}")


def cmd_lint(a):
    from .tells import detect, penalty

    worst = 0
    for path in a.files:
        html = Path(path).read_text(errors="ignore")
        styles = None
        sp = Path(path).with_name("styles.json")
        if sp.exists():
            styles = json.loads(sp.read_text())
        found = detect(html, styles)
        worst = max(worst, penalty(found))
        print(f"{path}: {len(found)} tells, penalty {penalty(found)}")
        for t in found:
            print(f"  [{'!' * t.severity:<3}] {t.name:<24} {t.evidence}")
    sys.exit(1 if a.strict and worst else 0)


def cmd_dataset(a):
    from .dataset import build

    print(json.dumps(build(min_score=a.min_score), indent=2))


def cmd_finetune(a):
    from .finetune import fuse, lora

    if a.fuse:
        fuse(a.model, a.name)
    else:
        lora(a.model, iters=a.iters, layers=a.layers, lr=a.lr, max_seq=a.max_seq, name=a.name, extra=a.extra)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="notai", description="Generate web UI that doesn't look AI-generated.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("scrape", help="screenshot + extract styles from a list of sites")
    p.add_argument("--list", default=str(config.SITES / "good.txt"))
    p.add_argument("--source", default="good", choices=["good", "vibe"], help="label prior for these sites")
    p.add_argument("--limit", type=int)
    p.add_argument("--delay", type=float, default=2.0, help="seconds between sites")
    p.add_argument("--force", action="store_true", help="re-capture sites already on disk")
    p.add_argument("--no-mobile", action="store_true")
    p.set_defaults(fn=cmd_scrape)

    p = sub.add_parser("negatives", help="generate archetypal vibecoded pages as negative examples")
    _backend_args(p)
    p.add_argument("--briefs", default=str(config.BRIEFS))
    p.add_argument("--limit", type=int)
    p.set_defaults(fn=cmd_negatives)

    p = sub.add_parser("label", help="open the labeling app")
    p.add_argument("--mode", default="single", choices=["single", "pair"])
    p.add_argument("--port", type=int, default=8765)
    p.set_defaults(fn=cmd_label)

    p = sub.add_parser("critic", help="train the critic or score pages")
    p.add_argument("action", choices=["train", "score", "info"])
    p.add_argument("paths", nargs="*", help="run dirs or screenshots to score")
    p.add_argument("--embed-model", default=config.DEFAULT_EMBED_MODEL)
    p.add_argument("--C", type=float, default=0.5, help="inverse regularization strength")
    p.set_defaults(fn=cmd_critic)

    p = sub.add_parser("stylebook", help="cluster good sites into style families")
    p.add_argument("-k", type=int, help="number of families (default: sites/8, 4–16)")
    p.add_argument("--embeddings", action="store_true", help="also cluster on cached image embeddings")
    p.set_defaults(fn=cmd_stylebook)

    p = sub.add_parser("families", help="list available style families")
    p.set_defaults(fn=cmd_families)

    p = sub.add_parser("generate", help="generate a page for a brief")
    p.add_argument("brief")
    _backend_args(p)
    p.add_argument("--family", default="auto")
    p.add_argument("-n", type=int, default=3, help="candidates per round")
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--target", type=float, default=0.85, help="stop when the score reaches this")
    p.add_argument("--critique-with", choices=["anthropic"], help="use this backend for screenshot critiques")
    p.set_defaults(fn=cmd_generate)

    p = sub.add_parser("batch", help="run generate for every brief in a file")
    _backend_args(p)
    p.add_argument("--briefs", default=str(config.BRIEFS))
    p.add_argument("--limit", type=int)
    p.add_argument("--family", default="auto")
    p.add_argument("-n", type=int, default=3)
    p.add_argument("--rounds", type=int, default=2)
    p.add_argument("--target", type=float, default=0.85)
    p.set_defaults(fn=cmd_batch)

    p = sub.add_parser("lint", help="list vibecoded tells in HTML files (no dependencies)")
    p.add_argument("files", nargs="+")
    p.add_argument("--strict", action="store_true", help="exit 1 if any tell is found")
    p.set_defaults(fn=cmd_lint)

    p = sub.add_parser("dataset", help="build the fine-tuning set from generations")
    p.add_argument("action", choices=["build"])
    p.add_argument("--min-score", type=float, default=0.8)
    p.set_defaults(fn=cmd_dataset)

    p = sub.add_parser("finetune", help="LoRA fine-tune a local model with mlx-lm")
    p.add_argument("--model", default=config.DEFAULT_MLX_MODEL)
    p.add_argument("--iters", type=int, default=600)
    p.add_argument("--layers", type=int, default=16)
    p.add_argument("--lr", type=float, default=1e-5)
    p.add_argument("--max-seq", type=int, default=8192)
    p.add_argument("--name", default="notai")
    p.add_argument("--fuse", action="store_true", help="fuse an existing adapter into the base model")
    p.add_argument("extra", nargs=argparse.REMAINDER, help="extra args passed to mlx_lm lora")
    p.set_defaults(fn=cmd_finetune)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
