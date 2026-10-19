# Beauty

Avoiding AI clichés gets you to "clean". Beautiful takes more: a page someone screenshots and sends to a
friend. Every page needs the things below. Avoid timid: when in doubt, make the centerpiece bigger, the color
more confident and the details finer.

## 1. A centerpiece visual (required)

Every page has one visual that someone remembers. It's built in code and it's rich: layered, detailed, specific
to this brand or product. Never a lone icon, a flat rectangle or a blob. Pick one:

- **An illustrated scene** in inline SVG: several layers (background shapes, midground objects, foreground
  details), a limited palette with 2–3 tones of each color for light and shade, small details that reward a
  second look (steam from a cup, a price tag, a pencil mark, grain).
- **The product, staged:** the real UI built in HTML/CSS at full fidelity, then presented with depth: tilted
  with `perspective` and `rotateX/Y`, floating panels overlapping at different depths, a soft colored shadow,
  a detail callout. For an app: show the most delightful moment (a streak, a completed deck, a chart going up).
- **A typographic composition:** one word or number set huge, cropped by the viewport, layered with a second
  typeface, outlined text, or an image clipped inside the letters.
- **Generative art:** an SVG or CSS pattern made from the brand's own motif (sardines in a tiling grid, kiln
  flames as concentric rings, a constellation of study topics), with variation in size, rotation and color.
- **A CSS object:** a convincing physical thing built with gradients and shadows: a ticket, a book cover, a
  card stack, a vinyl record, a phone, a jar label.

## 2. Depth and layering

Flat pages look unfinished. Create planes:
- Overlap elements across section boundaries (a card that hangs half into the next section, a visual that
  breaks the container).
- Layered, soft shadows that match the light: `box-shadow: 0 1px 2px rgb(0 0 0 / .06), 0 8px 24px -8px
  rgb(40 20 0 / .18)` tinted toward the palette, never default gray `0 10px 30px`.
- Subtle surfaces: a 1px inner highlight (`inset 0 1px 0 rgb(255 255 255 / .5)`), a hairline border, a
  slightly different paper tone per layer.

## 3. Texture and atmosphere

- A whisper of grain over large flat areas (an SVG `feTurbulence` noise as a background image at 3–6% opacity).
- Gradients are welcome when they're **subtle and on-palette**: a background that drifts from cream to a
  warmer cream, a radial light behind the centerpiece, a duotone. Banned only: purple/blue/pink AI gradients,
  gradient text, neon glow.
- Fine details: hairline rules, tick marks, small labels, a dotted leader in a price list, a stamp, a
  hand-drawn underline (an SVG path) under one key word.

## 4. Color with conviction

- One **color moment** per screen: a full section in the signature color, a big shape behind the centerpiece,
  a colored band. Large areas of a confident color look designed; sprinkles of accent look timid.
- Build tints and shades of each palette color (light, base, deep) and use them for layering.
- Dark sections are great for rhythm: alternate light and dark at least once on long pages.

## 5. Typography with finesse

- Big contrast in size between display and text (5–8× on landing pages), tight display tracking (-0.02 to
  -0.04em), optical sizes when the font has them (`font-optical-sizing: auto`).
- Mix in one expressive moment: an italic word in the headline, a second typeface for a pull quote, a number
  set very large.
- `text-wrap: balance` on headings, `text-wrap: pretty` on paragraphs, `font-variant-numeric: tabular-nums`
  for prices and data, hanging punctuation for quotes.

## 6. Motion and interaction

Pages should feel alive, quietly:
- An entrance: the centerpiece and headline fade/rise in once on load (CSS `@keyframes`, 400–700ms,
  `cubic-bezier(.2,.7,.2,1)`), staggered by 60–100ms. Respect `prefers-reduced-motion`.
- Hover states on every interactive element: a lift, an underline that draws in, an arrow that nudges.
- One ambient detail if it fits: steam that drifts, a timer that ticks, a marquee of real content.
- Never require motion to read content; never animate on scroll in a way that hides content in a screenshot.

## 7. Composition

- A strong grid with deliberate breaks. Vary section layouts: split, full-bleed, offset, stacked, a band.
- Generous space around the centerpiece; density where information lives.
- Something should cross a line on purpose — a visual over a section edge, a heading over an image.

## The beauty pass (after the checks are clean)

Look at the screenshots and ask, one by one. Fix every "no".
1. Is there one centerpiece someone would remember? Is it rich (layers, detail), not a single icon?
2. Is there depth — at least one overlap and one soft, palette-tinted shadow or layered surface?
3. Is there a color moment — a big confident area of the signature color?
4. Does the type have one expressive moment and real size contrast?
5. Is there texture or fine detail somewhere (grain, hairlines, labels, a drawn underline)?
6. Do interactive elements have hover states, and is there a gentle entrance?
7. Would this make someone stop scrolling? If it's merely tidy, push the centerpiece and color further.
