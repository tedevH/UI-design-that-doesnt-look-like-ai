"""Model backends: Ollama (local), MLX (local, with your LoRA adapter), Anthropic (optional API)."""

from __future__ import annotations

import base64
from pathlib import Path

from . import config
from .config import need
from .prompts import CRITIQUE_SYSTEM


class Backend:
    name = "base"

    def complete(self, system: str, messages: list[dict], temperature: float = 0.8, max_tokens: int = 12000) -> str:
        raise NotImplementedError

    def critique(self, png: Path) -> str | None:
        """Art-director notes on a screenshot, or None if this backend can't see images."""
        return None


class Ollama(Backend):
    name = "ollama"

    def __init__(self, model: str = config.DEFAULT_OLLAMA_MODEL, vision_model: str | None = None,
                 host: str = "http://127.0.0.1:11434"):
        self.model, self.vision_model, self.host = model, vision_model, host.rstrip("/")
        self.httpx = need("httpx", "generate")

    def _chat(self, model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
        try:
            r = self.httpx.post(
                f"{self.host}/api/chat",
                json={"model": model, "messages": messages, "stream": False,
                      "options": {"temperature": temperature, "num_ctx": 16384, "num_predict": max_tokens}},
                timeout=900,
            )
        except self.httpx.ConnectError:
            raise SystemExit(f"Can't reach Ollama at {self.host}. Start it (`ollama serve`) and `ollama pull {model}`.") from None
        if r.status_code == 404:
            raise SystemExit(f"Ollama doesn't have '{model}'. Run:  ollama pull {model}")
        r.raise_for_status()
        return r.json()["message"]["content"]

    def complete(self, system, messages, temperature=0.8, max_tokens=12000):
        return self._chat(self.model, [{"role": "system", "content": system}, *messages], temperature, max_tokens)

    def critique(self, png):
        if not self.vision_model:
            return None
        img = base64.b64encode(Path(png).read_bytes()).decode()
        return self._chat(self.vision_model, [
            {"role": "system", "content": CRITIQUE_SYSTEM},
            {"role": "user", "content": "Critique this page.", "images": [img]},
        ], 0.3, 800)


class MLX(Backend):
    """Runs a local model (optionally with a LoRA adapter from `notai finetune`) in-process."""

    name = "mlx"

    def __init__(self, model: str = config.DEFAULT_MLX_MODEL, adapter: str | None = None):
        mlx_lm = need("mlx_lm", "finetune")
        self._mlx_lm = mlx_lm
        self.model, self.tokenizer = mlx_lm.load(model, adapter_path=adapter)

    def complete(self, system, messages, temperature=0.8, max_tokens=12000):
        prompt = self.tokenizer.apply_chat_template(
            [{"role": "system", "content": system}, *messages], add_generation_prompt=True, tokenize=False)
        try:
            from mlx_lm.sample_utils import make_sampler

            return self._mlx_lm.generate(self.model, self.tokenizer, prompt=prompt, max_tokens=max_tokens,
                                         sampler=make_sampler(temp=temperature, top_p=0.95))
        except ImportError:  # older mlx-lm
            return self._mlx_lm.generate(self.model, self.tokenizer, prompt=prompt, max_tokens=max_tokens, temp=temperature)


class Anthropic(Backend):
    """Optional: Claude via the official SDK. Uses ANTHROPIC_API_KEY or an `ant auth login` profile."""

    name = "anthropic"

    def __init__(self, model: str = config.DEFAULT_ANTHROPIC_MODEL, effort: str = "high"):
        anthropic = need("anthropic", "api")
        self.client = anthropic.Anthropic()
        self.model, self.effort = model, effort

    def _run(self, system: str, messages: list[dict], max_tokens: int) -> str:
        # Streaming avoids HTTP timeouts on long HTML outputs. Server-side fallbacks re-run a
        # declined request on a fallback model inside the same call.
        with self.client.beta.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            thinking={"type": "adaptive"},
            output_config={"effort": self.effort},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "refusal":
            raise RuntimeError("The model declined this request.")
        return "".join(b.text for b in msg.content if b.type == "text")

    def complete(self, system, messages, temperature=0.8, max_tokens=32000):
        # temperature is ignored: current Claude models don't accept sampling parameters.
        return self._run(system, messages, max(max_tokens, 32000))

    def critique(self, png):
        img = base64.b64encode(Path(png).read_bytes()).decode()
        return self._run(CRITIQUE_SYSTEM, [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img}},
            {"type": "text", "text": "Critique this page."},
        ]}], 8000)


def make(name: str, model: str | None = None, adapter: str | None = None, vision_model: str | None = None) -> Backend:
    if name == "ollama":
        return Ollama(model or config.DEFAULT_OLLAMA_MODEL, vision_model=vision_model)
    if name == "mlx":
        return MLX(model or config.DEFAULT_MLX_MODEL, adapter=adapter)
    if name == "anthropic":
        return Anthropic(model or config.DEFAULT_ANTHROPIC_MODEL)
    raise SystemExit(f"Unknown backend '{name}' (use ollama, mlx, or anthropic)")
