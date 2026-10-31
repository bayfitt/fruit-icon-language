const test = require('node:test');
const assert = require('node:assert/strict');
const plan = require('../data/icon-colors.json');
const {luminance, contrast} = require('../scripts/palette.cjs');

test('every inventoried identity has a distinct exterior hue spread evenly across the wheel', () => {
  assert.equal(plan.icons.length, plan.counts.total);
  assert.equal(new Set(plan.icons.map(icon => icon.id)).size, plan.icons.length);
  assert.equal(new Set(plan.icons.map(icon => icon.colors.hue)).size, plan.icons.length);
  const buckets = Array(12).fill(0);
  for (const icon of plan.icons) buckets[Math.floor(icon.colors.hue / 30)]++;
  assert.ok(Math.max(...buckets) - Math.min(...buckets) <= 1);
});

test('major icon groups also cover the hue wheel evenly', () => {
  const groups = [
    plan.icons.filter(x => x.category === 'lucide'),
    plan.icons.filter(x => x.category === 'bundled-file-icon' && x.resolverSampled),
    plan.icons.filter(x => x.category === 'bundled-file-icon' && !x.resolverSampled),
    plan.icons.filter(x => x.category !== 'bundled-file-icon' && x.category !== 'lucide'),
  ];
  for (const group of groups) {
    const buckets = Array(12).fill(0);
    for (const icon of group) buckets[Math.floor(icon.colors.hue / 30)]++;
    assert.ok(Math.max(...buckets) - Math.min(...buckets) <= 1);
  }
});

test('proposed solid colors are saturated and contrast with black and with their accent', () => {
  for (const {id, colors} of plan.icons) {
    const body = colors, accent = colors.accent;
    assert.equal(body.saturation, 100, id);
    assert.equal(accent.saturation, 100, id);
    const b = luminance(body.hue, body.lightness), a = luminance(accent.hue, accent.lightness);
    assert.ok(contrast(b, 0) >= 3.2, id + ' body');
    assert.ok(contrast(a, 0) >= 3.2, id + ' accent');
    assert.ok(contrast(a, b) >= 3.2, id + ' parts');
    const separation = Math.abs(body.hue - accent.hue);
    assert.ok(Math.min(separation, 360 - separation) >= 149.99, id + ' near-complement');
  }
});

test('semantic roles and bundled icon sources are represented without claiming all are reachable', () => {
  for (const id of ['lucide:search','lucide:folder-plus','lucide:folder-open','role:composer-stop','role:window-maximize','role:attachment-remove','file-type:typescript']) {
    assert.ok(plan.icons.some(icon => icon.id === id), id);
  }
  assert.equal(plan.counts['bundled-file-icon'], 910);
  assert.equal(plan.counts.sampledResolvableFileIcons, 435);
});
