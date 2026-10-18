// Computed-style extraction. Evaluated in the page by Playwright; returns plain JSON.
// Aggregates design decisions (type, color, radius, spacing, layout) rather than markup.
() => {
  const MAX_ELEMENTS = 5000;
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const docHeight = Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0);

  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 1;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  const colorCache = new Map();
  // Normalizes any CSS color (rgb, oklch, color(), named) to #rrggbb, or null if mostly transparent.
  const toHex = (c) => {
    if (!c || c === "transparent") return null;
    if (colorCache.has(c)) return colorCache.get(c);
    ctx.clearRect(0, 0, 1, 1);
    ctx.fillStyle = "#000";
    ctx.fillStyle = c;
    ctx.fillRect(0, 0, 1, 1);
    const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
    const hex = a < 128 ? null : "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");
    colorCache.set(c, hex);
    return hex;
  };

  const bump = (obj, key, n = 1) => {
    if (key === null || key === undefined || key === "") return;
    obj[key] = (obj[key] || 0) + n;
  };
  const firstFamily = (stack) => stack.split(",")[0].replace(/["']/g, "").trim().toLowerCase();
  const px = (v) => parseFloat(v) || 0;
  const emojiRe = /\p{Extended_Pictographic}/gu;

  const out = {
    viewport: { w: vw, h: vh },
    docHeight,
    title: document.title || "",
    description: (document.querySelector('meta[name="description"]') || {}).content || "",
    fonts: {}, fontStacks: {}, fontSizes: {}, weights: {}, lineHeights: {}, letterSpacing: {},
    textColors: {}, bgColors: {}, gradients: [], gradientText: 0,
    radii: {}, boxes: 0, shadowedBoxes: 0, borderedBoxes: 0, blur: 0,
    spacing: {}, emoji: 0, words: 0, images: 0, svgs: 0,
    headings: [], rows: [], sections: 0, hero: null,
  };

  const visible = (el, r, cs) =>
    r.width > 1 && r.height > 1 && cs.visibility !== "hidden" && cs.display !== "none" && parseFloat(cs.opacity) > 0.05;

  const all = Array.from(document.body ? document.body.querySelectorAll("*") : []).slice(0, MAX_ELEMENTS);
  for (const el of all) {
    const tag = el.tagName.toLowerCase();
    if (["script", "style", "noscript", "template", "meta", "link"].includes(tag)) continue;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    if (!visible(el, r, cs)) continue;
    const area = Math.min(r.width, vw) * Math.min(r.height, docHeight);

    if (tag === "img" || tag === "picture" || tag === "video") out.images++;
    if (tag === "svg") out.svgs++;

    // Text: count only this element's own text nodes so nothing is double-counted.
    let own = "";
    for (const n of el.childNodes) if (n.nodeType === 3) own += n.textContent;
    own = own.trim();
    if (own) {
      const chars = own.length;
      out.words += own.split(/\s+/).length;
      out.emoji += (own.match(emojiRe) || []).length;
      bump(out.fonts, firstFamily(cs.fontFamily), chars);
      bump(out.fontStacks, cs.fontFamily, chars);
      const size = Math.round(px(cs.fontSize));
      bump(out.fontSizes, size, chars);
      bump(out.weights, cs.fontWeight, chars);
      if (cs.lineHeight !== "normal" && size) bump(out.lineHeights, (Math.round((px(cs.lineHeight) / size) * 20) / 20).toFixed(2), chars);
      if (cs.letterSpacing !== "normal" && size) bump(out.letterSpacing, (Math.round((px(cs.letterSpacing) / size) * 100) / 100).toFixed(2), chars);
      const tc = toHex(cs.color);
      if (tc) bump(out.textColors, tc, chars);
      if (cs.backgroundClip === "text" || cs.webkitBackgroundClip === "text") out.gradientText++;
    }

    // Boxes: anything with a visible background, border, or shadow.
    const bg = toHex(cs.backgroundColor);
    const hasBorder = px(cs.borderTopWidth) > 0 && toHex(cs.borderTopColor) !== null;
    const hasShadow = cs.boxShadow && cs.boxShadow !== "none";
    const bgImg = cs.backgroundImage || "none";
    if (bg) bump(out.bgColors, bg, Math.round(area / 100));
    if (bgImg.includes("gradient") && out.gradients.length < 60) out.gradients.push({ css: bgImg.slice(0, 300), area: Math.round(area) });
    if (bg || hasBorder || hasShadow || bgImg !== "none") {
      out.boxes++;
      if (hasShadow) out.shadowedBoxes++;
      if (hasBorder) out.borderedBoxes++;
      bump(out.radii, Math.round(px(cs.borderTopLeftRadius)));
    }
    const filt = (cs.backdropFilter || cs.webkitBackdropFilter || "") + " " + cs.filter;
    if (/blur\(/.test(filt)) out.blur++;

    for (const p of ["paddingTop", "paddingBottom", "paddingLeft", "marginTop", "marginBottom", "rowGap", "columnGap"]) {
      const v = Math.round(px(cs[p]));
      if (v > 0 && v < 400) bump(out.spacing, v);
    }

    if (/^h[1-3]$/.test(tag) && out.headings.length < 24 && el.innerText) {
      out.headings.push({
        tag, text: el.innerText.trim().slice(0, 140), size: Math.round(px(cs.fontSize)), weight: cs.fontWeight,
        align: cs.textAlign, family: firstFamily(cs.fontFamily), top: Math.round(r.top + window.scrollY), left: Math.round(r.left), cx: Math.round(r.left + r.width / 2),
      });
    }

    // Rows of 3+ same-size siblings side by side: the "three identical cards" pattern.
    const kids = Array.from(el.children).filter((k) => {
      const kr = k.getBoundingClientRect();
      return kr.width > 80 && kr.height > 80;
    });
    if (kids.length >= 3 && kids.length <= 8 && out.rows.length < 40) {
      const rects = kids.map((k) => k.getBoundingClientRect());
      const sameTop = rects.every((k) => Math.abs(k.top - rects[0].top) < 6);
      if (sameTop) {
        const ws = rects.map((k) => k.width), hs = rects.map((k) => k.height);
        const similar = Math.max(...ws) / Math.min(...ws) < 1.12 && Math.max(...hs) / Math.min(...hs) < 1.2;
        out.rows.push({ n: kids.length, w: Math.round(ws[0]), h: Math.round(hs[0]), similar, top: Math.round(rects[0].top + window.scrollY) });
      }
    }
  }

  // Sections: tall full-width blocks.
  const blocks = Array.from(document.querySelectorAll("body > *, main > *, body > div > *"));
  out.sections = blocks.filter((b) => {
    const r = b.getBoundingClientRect();
    return r.width > vw * 0.8 && r.height > 200;
  }).length;

  const h1 = out.headings.find((h) => h.tag === "h1") || out.headings[0];
  if (h1) {
    const centered = h1.align === "center" || (h1.left > vw * 0.15 && Math.abs(h1.cx - vw / 2) < 30);
    out.hero = { align: h1.align, centered, size: h1.size, family: h1.family, text: h1.text };
  }

  return out;
}
