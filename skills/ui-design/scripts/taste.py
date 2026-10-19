#!/usr/bin/env python3
"""Print the user's learned taste (creating it from the template on first use) and where it lives."""

from _env import bootstrap, ensure_taste

bootstrap(needs_env=False)
path = ensure_taste()
print(f"# taste file: {path}\n")
print(path.read_text())
