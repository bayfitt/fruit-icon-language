# One rounded plus fruit: Blender study

This is a static study of one plus-shaped fantasy fruit. The [render](./rounded-plus-study.png) shows the intact fruit, an oblique side view, and the two opened halves. The [Blender Python script](./build_rounded_plus.py) constructs and renders the same model; the saved `.blend` is kept locally because Blender files can contain local paths.

The [realistic material reference](./realistic-reference.png) is a separate AI-generated illustration based on an earlier Blender preview. It suggests a desired material finish; it is not a Blender render and does not prove the model's geometry. Its [prompts](./realistic-reference-prompt.md) are included.

The original fruit is a closed mesh with a rounded front and a rounded back. The skin, rind, flesh, central fleshy seed chamber, seed pockets and three differently shaped seeds are modeled as contained volumes. A single vertical cut produces both halves and the actual exposed seed sections. The one short stem is a separate closed mesh that intersects the skin and lies on one side of the cut. A single blossom-end mark is sampled in original-fruit coordinates so it is not duplicated as two whole marks.

The [geometry report](./geometry-report.json) records mesh, containment, volume, side-profile and camera checks. It also compares the cut boundaries and volumes of each pair of seed sections. These checks establish properties of this model, not biological authenticity, a polished final artwork, or accessibility at app-icon size. The chamber is filled tissue rather than an empty cavity, and the precise seed arrangement here is only one possibility; other fantasy fruits should have varied structures.

Spot checks of the full-size render found some seed/flesh and rind/flesh samples near or just below 3:1, and some darker outer-edge samples below 3:1 against black. These are isolated measurements, not a complete contrast audit. The texture and seed structure need further refinement and testing at actual icon sizes and states.

The [textures](./textures/README.md) were generated as material references. Blender is used here for one geometry study; the entire icon set does not have to be 3D-rendered.

From the repository root, regenerate the scene, report and render with Blender 4.5 LTS:

```sh
blender --background --factory-startup --threads 2 --python-exit-code 1 --python studies/rounded-plus/build_rounded_plus.py
```

Set `FRUIT_STUDY_SKIP_RENDER=1` to build the scene and run the geometry checks without rendering.
