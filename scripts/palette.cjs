// Color math for the design plan; it does not validate rendered concept art.
function luminance(h, l) {
  const lightness = l / 100;
  const chroma = 1 - Math.abs(2 * lightness - 1);
  const x = chroma * (1 - Math.abs((h / 60) % 2 - 1));
  const m = lightness - chroma / 2;
  const rgb = h < 60 ? [chroma,x,0] : h < 120 ? [x,chroma,0] : h < 180 ? [0,chroma,x] : h < 240 ? [0,x,chroma] : h < 300 ? [x,0,chroma] : [chroma,0,x];
  const linear = rgb.map(value => { value += m; return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4; });
  return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2];
}
function contrast(a, b) { return (Math.max(a, b) + .05) / (Math.min(a, b) + .05); }
function hsl(h, l) { return `hsl(${Number(h.toFixed(4))} 100% ${l}%)`; }

// Search moderately bright HSL colors. A near-complement may work better than
// the exact complement; both parts and their adjacency get an explicit margin.
function choosePair(hue) {
  let best;
  const lightnesses = Array.from({length: 37}, (_, i) => i + 33);
  const primary = lightnesses.map(l => ({l, lum: luminance(hue, l)})).filter(x => contrast(x.lum, 0) >= 3.25);
  for (const offset of [180, 165, 195, 150, 210]) {
    const accentHue = (hue + offset) % 360;
    const accents = lightnesses.map(l => ({l, lum: luminance(accentHue, l)})).filter(x => contrast(x.lum, 0) >= 3.25);
    for (const body of primary) for (const accent of accents) {
      const pairRatio = contrast(body.lum, accent.lum);
      if (pairRatio < 3.25) continue;
      const score = Math.abs(body.l - 49) + Math.abs(accent.l - 49) + Math.abs(180 - offset) * .035 + Math.abs(pairRatio - 3.8) * .3;
      if (!best || score < best.score) best = {score, body, accent, accentHue, pairRatio};
    }
  }
  if (!best) throw Error(`No accessible color pair for hue ${hue}`);
  const round = value => Math.round(value * 1000) / 1000;
  return {
    hue: Number(hue.toFixed(4)), saturation: 100, lightness: best.body.l,
    css: hsl(hue, best.body.l), blackContrast: round(contrast(best.body.lum, 0)),
    accent: {hue: Number(best.accentHue.toFixed(4)), saturation: 100, lightness: best.accent.l, css: hsl(best.accentHue, best.accent.l), blackContrast: round(contrast(best.accent.lum, 0))},
    partContrast: round(best.pairRatio),
  };
}
module.exports = {luminance, contrast, choosePair};
