"""Free local photos: FLUX.1-schnell (4-bit, Apache-2.0) running on Apple Silicon through mflux.

The model loads once per process (~10 GB of weights) and then makes a photo in roughly 10–40 seconds.
"""

from __future__ import annotations

import threading
from pathlib import Path

REPO = "madroid/flux.1-schnell-mflux-4bit"
_model = None
_lock = threading.Lock()  # one image at a time: the model isn't thread-safe and memory is shared

# Long side ~1024px, both sides multiples of 64.
SIZES = {
    "1:1": (1024, 1024), "4:3": (1024, 768), "3:4": (768, 1024), "3:2": (1152, 768), "2:3": (768, 1152),
    "16:9": (1216, 704), "9:16": (704, 1216), "21:9": (1344, 576), "4:5": (832, 1024), "5:4": (1024, 832),
}


def _load():
    global _model
    if _model is None:
        from huggingface_hub import snapshot_download
        from mflux.models.common.config import ModelConfig
        from mflux.models.flux.variants.txt2img.flux import Flux1

        path = snapshot_download(REPO)
        _model = Flux1(model_config=ModelConfig.from_name(model_name="schnell"), model_path=path)
    return _model


def generate(prompt: str, aspect: str, out: Path, steps: int = 4, seed: int | None = None) -> None:
    """Write a JPEG photo for `prompt` at `aspect` to `out`."""
    import hashlib

    from PIL import Image

    width, height = SIZES.get(aspect, SIZES["4:3"])
    seed = seed if seed is not None else int(hashlib.sha1(prompt.encode()).hexdigest()[:8], 16)
    with _lock:
        model = _load()
        img = model.generate_image(seed=seed, prompt=prompt, width=width, height=height, num_inference_steps=steps)
        tmp = Path(out).with_suffix(".png")
        img.save(path=str(tmp), export_json_metadata=False)
    Image.open(tmp).convert("RGB").save(out, "JPEG", quality=88)
    tmp.unlink(missing_ok=True)
