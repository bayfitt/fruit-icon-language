# One cut-open plus: geometry study

The [render](./cut-plus-geometry.png) compares one intact plus-shaped fantasy fruit with two pieces cut from the same shape. The [script](./build_cut_plus.py) recreates the Blender scene using its Python API. The generated `.blend` stays local because Blender files can contain absolute local paths. This is a static geometry study, not a finished icon or a small-size legibility and contrast test. Its interior is deliberately simple and still needs a more convincing fruit structure and texture.

The model is one closed, flat-backed plus with modeled skin, rind, and flesh. It is cut vertically through the middle, and the two real halves are turned outward 70 degrees around the back edge of the cut, then spaced apart slightly. A straight cut through this particular solid makes long, roughly rectangular cross-sections; it does not magically create half-plus-shaped cross-sections. The body is relatively thick to make the cut faces visible.

The [geometry report](./geometry-report.json) records manifold and volume checks, the angles, the direction of the cut faces relative to the camera, and framing checks. These checks support the geometry of this model; they do not establish accessibility or prove the visual quality of future artwork.

Reviewers found that the opened halves currently resemble two panels and may be hard to recognize as a plus at icon size. They recommend developing gently irregular rind boundaries and matching seedless fibers inside the actual cut surfaces. Representative rendered-pixel spot checks found roughly 1.22:1 at one rind/flesh boundary and 1.74:1 at one magenta edge against black, both below 3:1. These samples are not an exhaustive contrast audit; the future icon needs brighter silhouette edges, stronger part separation, and tests at actual sizes and states.

To regenerate the study with Blender 4.5 LTS, run from the repository root:

```sh
blender --background --factory-startup --threads 2 --python-exit-code 1 --python studies/cut-plus/build_cut_plus.py
```

The script writes the `.blend`, PNG, and JSON report beside itself. A portable Blender install can be invoked by specifying the path to its executable instead of adding it to `PATH`.
