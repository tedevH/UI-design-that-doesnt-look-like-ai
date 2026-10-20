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

  // Overlapping text: pairs of separate text elements whose boxes intersect substantially (layout bugs,
  // headers covering headlines). Only the first few screens, where it matters most.
  const texts = [];
  for (const el of all) {
    if (texts.length >= 600) break;
    let own = "";
    for (const n of el.childNodes) if (n.nodeType === 3) own += n.textContent;
    if (own.trim().length < 2) continue;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    if (!visible(el, r, cs) || r.top + window.scrollY > vh * 4 || r.width > vw * 1.05) continue;
    // Per-fragment boxes: a paragraph split across CSS columns or lines must not count as one big box.
    // Measure the glyphs themselves (ranges over the element's own text nodes), not the element's box:
    // a full-width paragraph next to a margin note must not count as overlapping it.
    const rects = [];
    for (const n of el.childNodes) {
      if (n.nodeType !== 3 || !n.textContent.trim()) continue;
      const range = document.createRange(); range.selectNodeContents(n);
      for (const q of range.getClientRects()) if (q.width > 1 && q.height > 1) rects.push(q);
    }
    texts.push({ el, rects });
  }
  const hit = (a, b) => {
    for (const p of a) for (const q of b) {
      const w = Math.min(p.right, q.right) - Math.max(p.left, q.left);
      const h = Math.min(p.bottom, q.bottom) - Math.max(p.top, q.top);
      if (w > 0 && h > 0 && w * h > 0.3 * Math.min(p.width * p.height, q.width * q.height)) return true;
    }
    return false;
  };
  let overlaps = 0;
  for (let i = 0; i < texts.length; i++) {
    for (let j = i + 1; j < texts.length; j++) {
      const a = texts[i], b = texts[j];
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
      if (hit(a.rects, b.rects)) overlaps++;
    }
  }
  out.overlaps = overlaps;

  // Text touching the viewport edge (missing side padding), measured on the glyphs.
  out.edgeText = [];
  for (const t of texts) {
    if (out.edgeText.length >= 5) break;
    // Only visible glyphs: skip text parked off-screen for screen readers.
    const onScreen = t.rects.filter((q) => q.right > 0 && q.left < vw && q.width > 1);
    if (onScreen.some((q) => q.left < 6 || q.right > vw - 6)) out.edgeText.push((t.el.innerText || "").trim().slice(0, 40));
  }

  // Buttons whose label wraps onto several lines (a phone number squeezed into a pill, etc.).
  out.wrappedButtons = [];
  for (const el of document.querySelectorAll("a, button")) {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    const looksLikeButton = (cs.backgroundColor !== "rgba(0, 0, 0, 0)" && cs.backgroundColor !== "transparent") ||
      parseFloat(cs.borderTopWidth) > 0 || parseFloat(cs.borderTopLeftRadius) >= 12;
    if (!looksLikeButton || r.width < 2 || r.height < 2 || !el.innerText.trim()) continue;
    // Intentionally multi-line buttons (label + sub-label in block children) are fine.
    if (Array.from(el.querySelectorAll("*")).some((c) => ["block", "flex", "grid", "list-item"].includes(getComputedStyle(c).display) && c.innerText?.trim())) continue;
    // Count distinct line boxes of the text itself (icons excluded).
    const tops = new Set();
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const n = walker.currentNode;
      if (!n.textContent.trim()) continue;
      const range = document.createRange(); range.selectNodeContents(n);
      for (const q of range.getClientRects()) if (q.width > 1) tops.add(Math.round(q.top / 4));
    }
    const lh = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.3;
    const textH = tops.size * lh;
    if (textH > lh * 1.8 && el.innerText.trim().length < 40) out.wrappedButtons.push(el.innerText.trim().replace(/\s+/g, " ").slice(0, 40));
  }

  // Icon cards: a box that opens with a small icon, then a heading — the feature-grid template.
  out.iconCards = 0;
  for (const el of all) {
    const first = el.firstElementChild;
    if (!first || el.children.length < 2) continue;
    const fr = first.getBoundingClientRect(), er = el.getBoundingClientRect();
    const small = fr.width > 0 && fr.width <= 64 && fr.height <= 64;
    const iconish = first.tagName === "svg" || first.querySelector?.("svg, img") || /icon/i.test(first.className?.baseVal ?? first.className ?? "");
    const heading = Array.from(el.children).slice(1, 3).some((c) => /^H[2-5]$/.test(c.tagName));
    if (small && iconish && heading && er.width < vw * 0.6) out.iconCards++;
  }

  // Icons: small SVG/icon-font glyphs. Functional ones live in nav, buttons, links and form controls;
  // the rest are decoration. Icon tiles are icons sitting in a small tinted rounded box.
  out.decorativeIcons = 0; out.iconTiles = 0; out.functionalIcons = 0;
  const iconEls = Array.from(document.querySelectorAll("svg, i[class], span[class*='icon'], [data-lucide], [class*='lucide'], [class*='fa-']"));
  for (const ic of iconEls) {
    if (ic.parentElement && ic.parentElement.closest("svg")) continue;  // nested svg parts
    const r = ic.getBoundingClientRect();
    if (r.width < 6 || r.height < 6 || r.width > 40 || r.height > 40) continue;  // big drawings are illustrations
    if (getComputedStyle(ic).display === "none") continue;
    if (ic.closest("nav, button, a, input, select, label, [role=button], [role=tab], header .logo, .brand, [class*='logo']")) { out.functionalIcons++; continue; }
    out.decorativeIcons++;
    const box = ic.parentElement;
    if (box) {
      const b = box.getBoundingClientRect(), bc = getComputedStyle(box);
      const tinted = bc.backgroundColor !== "rgba(0, 0, 0, 0)" && bc.backgroundColor !== "transparent";
      if (tinted && b.width <= 72 && b.height <= 72 && b.width >= r.width + 8 && parseFloat(bc.borderTopLeftRadius) >= 4) out.iconTiles++;
    }
  }

  const h1 = out.headings.find((h) => h.tag === "h1") || out.headings[0];
  if (h1) {
    const centered = h1.align === "center" || (h1.left > vw * 0.15 && Math.abs(h1.cx - vw / 2) < 30);
    out.hero = { align: h1.align, centered, size: h1.size, family: h1.family, text: h1.text };
  }

  // Objective checks to complement, not replace, visual inspection.
  const parseColor = (value) => {
    const m = value && value.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
    return m ? { r: +m[1], g: +m[2], b: +m[3], a: m[4] === undefined ? 1 : +m[4] } : null;
  };
  const composite = (fg, bg) => {
    const a = fg.a + bg.a * (1 - fg.a);
    if (!a) return { r: 0, g: 0, b: 0, a: 0 };
    return { r: (fg.r * fg.a + bg.r * bg.a * (1 - fg.a)) / a,
      g: (fg.g * fg.a + bg.g * bg.a * (1 - fg.a)) / a,
      b: (fg.b * fg.a + bg.b * bg.a * (1 - fg.a)) / a, a };
  };
  const luminance = (c) => {
    const channel = (n) => { n /= 255; return n <= 0.04045 ? n / 12.92 : Math.pow((n + 0.055) / 1.055, 2.4); };
    return 0.2126 * channel(c.r) + 0.7152 * channel(c.g) + 0.0722 * channel(c.b);
  };
  const contrast = (a, b) => {
    const x = luminance(a), y = luminance(b);
    return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
  };
  const backgroundFor = (el) => {
    const chain = [];
    for (let node = el; node && node.nodeType === 1; node = node.parentElement) {
      const cs = getComputedStyle(node);
      if (cs.backgroundImage && cs.backgroundImage !== "none") return null;
      if (parseFloat(cs.opacity) < 0.98) return null;
      chain.unshift(cs.backgroundColor);
    }
    let bg = { r: 255, g: 255, b: 255, a: 1 };
    for (const value of chain) { const color = parseColor(value); if (color) bg = composite(color, bg); }
    return bg;
  };
  const lowContrast = [];
  for (const el of all) {
    let own = "";
    for (const n of el.childNodes) if (n.nodeType === 3) own += n.textContent;
    own = own.trim();
    if (!own || !visible(el, el.getBoundingClientRect(), getComputedStyle(el)) || lowContrast.length >= 12) continue;
    const cs = getComputedStyle(el), fg = parseColor(cs.color), bg = backgroundFor(el);
    if (!fg || !bg || fg.a < 0.98) continue;
    const ratio = contrast(composite(fg, bg), bg);
    const size = px(cs.fontSize), weight = parseInt(cs.fontWeight, 10) || 400;
    const minimum = size >= 24 || (size >= 18.66 && weight >= 700) ? 3 : 4.5;
    if (ratio < minimum) lowContrast.push({ text: own.replace(/\s+/g, " ").slice(0, 48), ratio: Math.round(ratio * 100) / 100, minimum });
  }

  const unlabeledControls = [];
  const controls = Array.from(document.querySelectorAll('button, input:not([type="hidden"]), select, textarea, a[href], [role="button"], [role="link"]'));
  let targetsUnder24px = 0;
  for (const el of controls) {
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    if (!visible(el, r, cs)) continue;
    const labelledBy = (el.getAttribute("aria-labelledby") || "").split(/\s+/).filter(Boolean)
      .map((id) => document.getElementById(id)?.innerText || "").join(" ").trim();
    const labels = el.labels ? Array.from(el.labels).map((l) => l.innerText).join(" ").trim() : "";
    const imageAlt = Array.from(el.querySelectorAll("img[alt]")).map((img) => img.alt).join(" ").trim();
    const name = el.getAttribute("aria-label") || labelledBy || el.innerText?.trim() || el.value || el.title || labels || imageAlt;
    if (!name && unlabeledControls.length < 12) unlabeledControls.push(el.tagName.toLowerCase() + (el.type ? "[" + el.type + "]" : ""));
    if (r.width < 24 || r.height < 24) targetsUnder24px++;
  }
  const visibleImages = Array.from(document.images).filter((img) => visible(img, img.getBoundingClientRect(), getComputedStyle(img)));
  out.audit = {
    viewportWidth: vw,
    scrollWidth: document.documentElement.scrollWidth,
    documentTitle: document.title.trim(),
    documentLanguage: document.documentElement.lang.trim(),
    h1Count: Array.from(document.querySelectorAll("h1")).filter((el) => visible(el, el.getBoundingClientRect(), getComputedStyle(el))).length,
    imagesMissingAlt: visibleImages.filter((img) => !img.hasAttribute("alt")).length,
    brokenImages: visibleImages.filter((img) => (img.currentSrc || img.src) && img.complete && img.naturalWidth === 0).map((img) => img.currentSrc || img.src).slice(0, 8),
    unlabeledControls,
    targetsUnder24px,
    lowContrast
  };

  return out;
}
