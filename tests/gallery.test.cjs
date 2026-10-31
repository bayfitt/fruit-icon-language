const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '..');

test('the gallery shows the current exterior study and its asset exists', () => {
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  const references = [...html.matchAll(/(?:src|href)="\.\/([^"]+)"/g)].map(match => match[1]);
  assert.ok(references.includes('assets/fruit-skin-variations.png'));
  for (const reference of references) assert.ok(fs.existsSync(path.join(root, reference)), reference);
  assert.doesNotMatch(html, /fruit-interior-earlier-study|structural-plastic-study/);
});

test('authored HSL colors are saturated and normal text contrasts with black', () => {
  const css = fs.readFileSync(path.join(root, 'assets', 'gallery.css'), 'utf8');
  const colors = [...css.matchAll(/hsl\((\d+)\s+(\d+)%\s+(\d+)%\)/g)].map(match => match.slice(1).map(Number));
  assert.ok(colors.length > 5);
  assert.ok(colors.every(([, saturation]) => saturation === 100));
  function contrastOnBlack(hue, lightness) {
    const l = lightness / 100, c = 1 - Math.abs(2 * l - 1), x = c * (1 - Math.abs((hue / 60) % 2 - 1)), m = l - c / 2;
    const rgb = hue < 60 ? [c,x,0] : hue < 120 ? [x,c,0] : hue < 180 ? [0,c,x] : hue < 240 ? [0,x,c] : hue < 300 ? [x,0,c] : [c,0,x];
    const lin = rgb.map(v => { v += m; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; });
    return (0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2] + .05) / .05;
  }
  for (const [hue, lightness] of [[185,65], [315,70], [55,62]]) assert.ok(contrastOnBlack(hue, lightness) >= 4.5);
});
