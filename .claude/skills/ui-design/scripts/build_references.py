#!/usr/bin/env python3
"""Regenerate references/families.md from notai's style families and the best design notes per family.
Run again after `notai notes` has studied more sites."""

import sys

from _notai import SKILL, bootstrap

bootstrap()

from notai import notes  # noqa: E402
from notai.families import FAMILIES  # noqa: E402


def main() -> int:
    out = ["# Style families", "",
           "Pick two different families per brief. Each lists its look, its typography, and notes on strong real",
           "sites in the family (written by a local vision model from screenshots). Learn the principles; never copy.", ""]
    for f in FAMILIES:
        out += [f"## {f['id']} — {f['name']}", "", f"**Look:** {f['look']}", "", f"**Typography:** {f['type']}", ""]
        strong = notes.for_family(f["id"], min_quality=7, k=3)
        if strong:
            out.append("**Strong real sites:**")
            out.append("")
            for n in strong:
                out.append("- " + notes.as_text(n).replace("\n", "\n  "))
            out.append("")
        else:
            out += [f"**References:** {', '.join(f['refs'])}", ""]
    (SKILL / "references" / "families.md").write_text("\n".join(out))
    print(f"wrote {SKILL / 'references' / 'families.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
