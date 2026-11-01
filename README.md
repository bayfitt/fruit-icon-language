# Fruit Icon Language

A design exploration for colorful alien fantasy-fruit computer icons on a pure black background. The current focus is on richly textured exterior skins.

Open [index.html](./index.html) in a browser. The current gallery shows only the outside of the fantasy fruits. Earlier inside and plastic concept sheets are preserved in [archive](./archive) for possible future work. The gallery has no build dependencies. A [single rounded plus fruit study](./studies/rounded-plus/README.md) includes a reproducible Blender model, cut seed structure and geometry checks; an [earlier flat-backed study](./studies/cut-plus/README.md) is retained for history.

The [color plan](./colors.html) can be searched in a browser. It proposes a unique, evenly spaced exterior hue and an initial contrast-checked accent for 1,043 catalog entries. The existing accent suggestions are complementary or near-complementary starting points, not a requirement: the user also wants neighboring and other varied hues. These are not 1,043 proven distinct visible controls: entries include overlapping semantic roles and alternate bundled assets. The snapshot includes 84 Lucide icons and all 910 bundled file-type assets; the latter are not necessarily all reachable (435 were resolved in a sample of the package's mappings). It also records custom SVGs, launch choices, bundled app targets, and some semantic/native roles. Dynamic app icons and other runtime or CSS-generated graphics cannot be guaranteed exhaustive from a static checkout. Numerically different hues may look similar to a person. These are proposed color tokens, not finished icons or proof of rendered contrast.

The snapshot is in [data/icon-colors.json](./data/icon-colors.json), derived from the recorded CodexMonitor commit and installed icon-package versions. To reproduce it, run `node scripts/inventory-codexmonitor.cjs PATH_TO_CODEXMONITOR` with that checkout's dependencies installed. Assignments are frozen: do not reshuffle existing hues merely because future icons are added.

With Node.js installed, run `node --test tests/*.test.cjs` to check the gallery, hue distribution and proposed solid-color contrasts.

The images are concept art, not a finished icon pack. Individual icon assets, application integration, small-size rendering, and accessibility verification remain work to do. The gallery does not change Codex Monitor.

Read [DESIGN.md](./DESIGN.md) for the principles and constraints and [PROMPTS.md](./PROMPTS.md) for the concept-art prompt. Project-scoped Codex reviewer definitions live in [the agents directory](./.codex/agents); they can be used when working in a trusted project and are invoked during design work rather than running continuously. Artwork and gallery code are available under the [MIT license](./LICENSE).
