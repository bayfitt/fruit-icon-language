// Snapshot source identities, then propose one unique hue per known identity.
// Usage: node scripts/inventory-codexmonitor.cjs PATH_TO_CODEXMONITOR
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const {choosePair} = require('./palette.cjs');

const repo = process.argv[2] && path.resolve(process.argv[2]);
if (!repo) throw Error('Supply the CodexMonitor checkout path.');
const git = (...args) => execFileSync('git', args, {cwd: repo, encoding: 'utf8', maxBuffer: 32 * 1024 * 1024}).trim();
const revision = git('rev-parse', 'HEAD');
const iconsDir = path.join(repo, 'node_modules', 'vscode-material-icons', 'generated', 'icons');
if (!fs.existsSync(iconsDir)) throw Error('Install the checkout dependencies before inventorying file-type icons.');
const iconMap = require(path.join(repo, 'node_modules', 'vscode-material-icons', 'generated', 'icon-map.json'));
const material = require(path.join(repo, 'node_modules', 'vscode-material-icons'));
const sampleNames = ['unmatched-unknown-file','x.html','x.ts','x.js', ...Object.keys(iconMap.fileNames), ...Object.keys(iconMap.fileExtensions).map(x => 'file.' + x)];
const sampleResolved = new Set(sampleNames.map(name => material.getIconForFilePath(name)));
const entries = new Map();
function add(id, category, source, extra = {}) {
  if (!entries.has(id)) entries.set(id, {id, category, sources: [], ...extra});
  if (source && !entries.get(id).sources.includes(source)) entries.get(id).sources.push(source);
}
function matches(line) {
  const found = /^HEAD:(.+?):(\d+):(.*)$/.exec(line);
  return found && !/\.(test|spec)\.[jt]sx?$/.test(found[1]) && !found[1].endsWith('.d.ts') ? found : null;
}
function kebab(name) { return name.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase(); }
for (const line of git('grep', '-n', 'lucide-react', 'HEAD', '--', 'src').split('\n')) {
  const hit = matches(line); if (!hit) continue;
  const source = `${hit[1]}:${hit[2]}`;
  const direct = /lucide-react\/dist\/esm\/icons\/([^"'\s]+)/.exec(hit[3]);
  if (direct) add('lucide:' + direct[1], 'lucide', source);
  const named = /import\s*\{([^}]+)\}\s*from\s*["']lucide-react["']/.exec(hit[3]);
  if (named) for (const part of named[1].split(',')) add('lucide:' + kebab(part.trim().split(/\s+as\s+/)[0]), 'lucide', source);
}
for (const line of git('grep', '-n', '<svg', 'HEAD', '--', 'src').split('\n')) {
  const hit = matches(line); if (!hit) continue;
  add(`inline:${hit[1]}:${hit[2]}`, hit[1].endsWith('openAppIcons.ts') ? 'encoded-svg' : 'inline-svg', `${hit[1]}:${hit[2]}`);
}
const launchSource = git('show', 'HEAD:src/features/app/utils/launchScriptIcons.ts');
const launchBlock = /const ICON_MAP[^=]*=\s*\{([\s\S]*?)\};/.exec(launchSource);
if (!launchBlock) throw Error('Could not find the launch icon map in committed source.');
for (const hit of launchBlock[1].matchAll(/^\s*(\w+):\s*(\w+)/gm)) add('launch:' + hit[1], 'launch-choice', 'src/features/app/utils/launchScriptIcons.ts', {sourceGlyph: hit[2]});
for (const file of git('ls-tree', '-r', '--name-only', 'HEAD', 'src/assets/app-icons').split('\n').filter(Boolean)) {
  add('app-target:' + path.basename(file, path.extname(file)), 'bundled-app-logo', file);
}
for (const file of fs.readdirSync(iconsDir).filter(file => file.endsWith('.svg')).sort()) {
  const name = file.slice(0, -4);
  add('file-type:' + name, 'bundled-file-icon', 'vscode-material-icons/generated/icons/' + file, {resolverSampled: sampleResolved.has(name)});
}
for (const [id, source] of [
  ['role:composer-send', 'src/features/composer/components/ComposerInput.tsx'],
  ['role:composer-stop', 'src/features/composer/components/ComposerInput.tsx'],
  ['role:window-maximize', 'src/features/layout/components/WindowCaptionControls.tsx'],
  ['role:window-close', 'src/features/layout/components/WindowCaptionControls.tsx'],
  ['role:attachment-remove', 'src/features/composer/components/ComposerAttachments.tsx'],
  ['role:dialog-close', 'src/features/settings/components/SettingsView.tsx'],
  ['role:tree-expand', 'src/features/app/components/WorkspaceCard.tsx'],
  ['role:tree-collapse', 'src/features/app/components/WorkspaceCard.tsx'],
  ['role:toast-dismiss', 'src/features/notifications'],
  ['role:terminal-close', 'src/features/terminal'],
  ['role:dropdown-caret', 'src/styles'],
  ['role:loading-spinner', 'src/styles'],
  ['role:status-indicator', 'src/styles'],
  ['native:application', 'src-tauri/icons/icon.ico'],
  ['native:tray', 'src-tauri/icons/tray-icon.png'],
  ['runtime:external-app-fallback', 'src/features/app/hooks/useOpenAppIcons.ts'],
]) add(id, 'semantic-or-runtime', source);

const list = [...entries.values()];
const frozenPath = path.join(__dirname, '..', 'data', 'icon-colors.json');
const previous = fs.existsSync(frozenPath) ? JSON.parse(fs.readFileSync(frozenPath, 'utf8')) : null;
function hash(text) { let h = 2166136261; for (const character of text) { h ^= character.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }
const byHash = (a, b) => hash(a.id) - hash(b.id) || a.id.localeCompare(b.id);
const count = list.length;
function group(item) {
  if (item.category === 'lucide') return 'lucide';
  if (item.category === 'bundled-file-icon') return item.resolverSampled ? 'file-sampled' : 'file-other';
  return 'other';
}
const anchors = {
  'lucide:refresh-cw': 125, 'lucide:search': 30, 'lucide:folder-plus': 275,
  'lucide:settings': 185, 'role:composer-send': 55, 'lucide:save': 225,
  'lucide:folder-open': 0, 'lucide:plus': 320,
};
if (previous) {
  // Preserve every existing assignment exactly; place new identities into the
  // largest unused gap in their least-populated hue family.
  const old = new Map(previous.icons.map(item => [item.id, item.colors]));
  const used = previous.icons.map(item => item.colors.hue);
  for (const item of list) if (old.has(item.id)) item.colors = old.get(item.id);
  for (const item of list.filter(item => !item.colors).sort(byHash)) {
    const familyCounts = Array(12).fill(0), allCounts = Array(12).fill(0);
    for (const existing of list.filter(x => x.colors)) {
      const family = Math.floor(existing.colors.hue / 30);
      allCounts[family]++;
      if (group(existing) === group(item)) familyCounts[family]++;
    }
    const family = [...Array(12).keys()].sort((a, b) => familyCounts[a] - familyCounts[b] || allCounts[a] - allCounts[b] || a - b)[0];
    const points = [family * 30, ...used.filter(h => h > family * 30 && h < (family + 1) * 30).sort((a, b) => a - b), (family + 1) * 30];
    let gap = -1, hue = family * 30 + 15;
    for (let i = 1; i < points.length; i++) if (points[i] - points[i - 1] > gap) { gap = points[i] - points[i - 1]; hue = (points[i] + points[i - 1]) / 2; }
    item.colors = choosePair(hue); used.push(item.colors.hue);
  }
} else {
  // Initial snapshot: every group is balanced by 30-degree family, and the
  // entire inventory occupies evenly spaced, unique slots around the wheel.
  const slots = Array.from({length: 12}, () => []);
  for (let i = 0; i < count; i++) slots[Math.floor(i * 12 / count)].push(i);
  const names = ['lucide', 'file-sampled', 'file-other', 'other'];
  const grouped = Object.fromEntries(names.map(name => [name, list.filter(item => group(item) === name).sort(byHash)]));
  const quotas = Object.fromEntries(names.map(name => [name, Array(12).fill(Math.floor(grouped[name].length / 12))]));
  const capacity = slots.map((bucket, family) => bucket.length - names.reduce((n, name) => n + quotas[name][family], 0));
  for (const name of names) {
    let extra = grouped[name].length % 12;
    const start = hash(name) % 12;
    const candidates = [...Array(12).keys()].sort((a, b) => capacity[b] - capacity[a] || ((a - start + 12) % 12) - ((b - start + 12) % 12));
    for (const family of candidates) if (extra && capacity[family] > 0) { quotas[name][family]++; capacity[family]--; extra--; }
    if (extra) throw Error('Unable to balance hue-family quotas.');
  }
  const assigned = new Map();
  for (const [id, desired] of Object.entries(anchors)) {
    const item = entries.get(id); if (!item) continue;
    const name = group(item), family = Math.floor(desired / 30);
    if (!quotas[name][family]) throw Error('No hue-family slot for anchor ' + id);
    const bucket = slots[family];
    const bestIndex = bucket.reduce((best, slot, i) => Math.abs(slot * 360 / count - desired) < Math.abs(bucket[best] * 360 / count - desired) ? i : best, 0);
    assigned.set(id, bucket.splice(bestIndex, 1)[0]); quotas[name][family]--;
  }
  for (const name of names) for (const item of grouped[name]) {
    if (assigned.has(item.id)) continue;
    const start = hash(item.id) % 12;
    const family = [...Array(12).keys()].map(i => (start + i * 5) % 12).find(index => quotas[name][index] > 0);
    const bucket = slots[family], index = hash(item.id + ':slot') % bucket.length;
    assigned.set(item.id, bucket.splice(index, 1)[0]); quotas[name][family]--;
  }
  for (const item of list) item.colors = choosePair(assigned.get(item.id) * 360 / count);
}
list.sort((a, b) => a.id.localeCompare(b.id));
const categoryCounts = Object.fromEntries([...new Set(list.map(x => x.category))].sort().map(category => [category, list.filter(x => x.category === category).length]));
const output = {
  description: 'Frozen proposed color assignments, not rendered or installed icons.',
  source: {repository: 'https://github.com/bayfitt/CodexMonitor', revision, lucideVersion: require(path.join(repo, 'node_modules', 'lucide-react', 'package.json')).version, materialVersion: require(path.join(repo, 'node_modules', 'vscode-material-icons', 'package.json')).version},
  method: 'One unique evenly spaced exterior hue per known identity, balanced within each inventory group; full-saturation body and near-complement accent. Repeated uses can share an identity. The 910 bundled file assets are not necessarily all reachable. Existing assignments are preserved when the inventory is refreshed.',
  limitations: ['Automated source inventory is not proof of every runtime or native icon.', 'Some source glyphs have multiple meanings and need separate semantic designs.', 'Unknown user-installed app icons and user-provided media are not statically enumerable.', 'Numbers are proposed solid HSL tokens, not measured rendered icon contrast.'],
  counts: {...categoryCounts, total: count, sampledResolvableFileIcons: sampleResolved.size},
  icons: list,
};
fs.mkdirSync(path.dirname(frozenPath), {recursive: true});
fs.writeFileSync(frozenPath, JSON.stringify(output, null, 2) + '\n');
const browserData = list.map(({id, category, colors}) => ({id, category, colors}));
fs.writeFileSync(path.join(path.dirname(frozenPath), 'icon-colors.js'), 'window.fruitIconColors = ' + JSON.stringify(browserData) + ';\n');
console.log(JSON.stringify(output.counts, null, 2));
