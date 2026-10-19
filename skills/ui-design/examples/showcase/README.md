# Fieldnote: North Cove station

An illustrative dashboard concept that demonstrates product-led visual direction in a data-heavy interface. It is a static HTML page with inline SVG, sample readings, and responsive CSS. The sample values are fictional; it is not a live tide forecast or an operational safety tool.

## Design decisions

- **Task:** Read the current water conditions and identify the next tide change.
- **Premise:** A coastal field log where the tide curve is the main visual object; observations feel recorded on paper, while measured data stays precise and scannable.
- **First read:** Station and time context, current water height, then observed-versus-predicted tide curve.
- **System:** Mineral paper, ink-blue text, muted sea green for observed data, and a restrained clay signal for forecast and current time. Serif display type gives the station a field-notes character; a neutral sans supports interface reading; mono is reserved for units and timestamps.
- **Composition:** Conditions are aligned as a compact signal row; the chart owns the main column; turning points and wind remain supporting facts in a narrower rail.
- **Responsive shift:** The navigation becomes a bottom bar, conditions form a two-by-two grid, and the chart precedes stacked supporting panels.
- **Interaction:** No decorative controls are presented as functional; this example is a static design study.

## Preview

Open `tide-station.html` in a browser. For a local visual audit, from `skills/ui-design/` run:

```bash
python3 scripts/check.py examples/showcase/tide-station.html --type app
```

The page uses Google Fonts when a network is available and includes system fallbacks. Review the typography again if the external font request is unavailable. The visual result has not yet been browser-reviewed in this repository, so treat this as a design specimen awaiting that pass.
