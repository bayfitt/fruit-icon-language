"""Make one physically cut fantasy-fruit plus in Blender, without animation.

Usage: blender --background --factory-startup --python build_cut_plus.py
The .blend, render, and geometry report are written beside this script.
"""
import bpy
import bmesh
import json
import math
import os
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from pathlib import Path

HERE = Path(__file__).resolve().parent
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def material(name, color, light_color, noise_scale, bump_strength, roughness=0.4):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = 0.25
    coordinates = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.68
    links.new(coordinates.outputs["Object"], noise.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.045
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    blush = nodes.new("ShaderNodeTexNoise")
    blush.inputs["Scale"].default_value = 3.5
    blush.inputs["Detail"].default_value = 4
    blush.inputs["Roughness"].default_value = 0.65
    links.new(coordinates.outputs["Object"], blush.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = (*color, 1)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (*light_color, 1)
    links.new(blush.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    return mat


skin = material("Magenta fantasy-fruit skin", (0.62, 0.0, 0.18), (0.82, 0.0, 0.28), 16, 0.28)
rind = material("Lime rind", (0.22, 0.56, 0.0), (0.42, 0.76, 0.0), 22, 0.15, 0.48)
flesh = material("Turquoise flesh", (0.0, 0.38, 0.35), (0.0, 0.72, 0.50), 12, 0.18, 0.42)


def plus_mesh(name, half_arm, reach, depth, bevel):
    """A closed, beveled plus with a planar back, in X/Z, with depth along Y."""
    a, b = half_arm, reach
    outline = [(-a, -b), (a, -b), (a, -a), (b, -a),
               (b, a), (a, a), (a, b), (-a, b),
               (-a, a), (-b, a), (-b, -a), (-a, -a)]
    count = len(outline)
    verts = [(x, -depth / 2, z) for x, z in outline]
    verts += [(x, depth / 2, z) for x, z in outline]
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    faces += [(i, (i + 1) % count, (i + 1) % count + count, i + count)
              for i in range(count)]
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    # Ensure a coherent outward orientation before the exact solid booleans.
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    mod = obj.modifiers.new("Soft organic edges", "BEVEL")
    mod.width = bevel
    mod.segments = 4
    mod.limit_method = "ANGLE"
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)
    return obj


def duplicate(obj, name):
    other = obj.copy()
    other.data = obj.data.copy()
    other.name = name
    bpy.context.collection.objects.link(other)
    return other


def apply_boolean(obj, cutter, operation):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    mod = obj.modifiers.new(operation + " solid", "BOOLEAN")
    mod.operation = operation
    mod.solver = "EXACT"
    mod.object = cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)


def mesh_stats(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    stats = {
        "volume": abs(bm.calc_volume(signed=True)),
        "nonmanifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "faces": len(bm.faces),
    }
    bm.free()
    return stats


outer = plus_mesh("Whole fruit solid", 0.62, 1.60, 1.60, 0.20)
middle = plus_mesh("Inside of skin", 0.49, 1.46, 1.30, 0.15)
core = plus_mesh("Inside of rind", 0.36, 1.32, 1.00, 0.10)
whole_stats = mesh_stats(outer)
assert whole_stats["nonmanifold_edges"] == 0

# The intact fruit uses the same outer solid as the one split below.
whole_display = duplicate(outer, "Intact fruit")
whole_display.data.materials.clear()
whole_display.data.materials.append(skin)
whole_display.location.x = -2.85
for face in whole_display.data.polygons:
    face.use_smooth = True

# Nested closed volumes make real skin, rind, and flesh; these are not decals.
skin_layer = duplicate(outer, "Skin before cut")
apply_boolean(skin_layer, middle, "DIFFERENCE")
skin_layer.data.materials.clear()
skin_layer.data.materials.append(skin)
rind_layer = duplicate(middle, "Rind before cut")
apply_boolean(rind_layer, core, "DIFFERENCE")
rind_layer.data.materials.clear()
rind_layer.data.materials.append(rind)
flesh_layer = duplicate(core, "Flesh before cut")
flesh_layer.data.materials.clear()
flesh_layer.data.materials.append(flesh)

layers = [("skin", skin_layer), ("rind", rind_layer), ("flesh", flesh_layer)]
before = {name: mesh_stats(obj) for name, obj in layers}


def halfspace(name, min_x, max_x):
    bpy.ops.mesh.primitive_cube_add(size=2, location=((min_x + max_x) / 2, 0, 0))
    cutter = bpy.context.object
    cutter.name = name
    cutter.dimensions = (max_x - min_x, 10, 10)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return cutter


left_cutter = halfspace("Left half-space x <= 0", -5, 0)
right_cutter = halfspace("Right half-space x >= 0", 0, 5)
after = {"left": {}, "right": {}}
cut_halves = []
hinge_y = 0.8  # back edge of the uncut fruit
gap = 0.10
for side, cutter, angle in (("left", left_cutter, -70), ("right", right_cutter, 70)):
    pivot = bpy.data.objects.new(side.title() + " cut rotation", None)
    bpy.context.collection.objects.link(pivot)
    # At zero rotation, each half sits where the one original solid was.
    pivot.location = (2.35 + (-gap if side == "left" else gap), hinge_y, 0)
    for name, layer in layers:
        half = duplicate(layer, side.title() + " " + name)
        apply_boolean(half, cutter, "INTERSECT")
        cut_halves.append(half)
        after[side][name] = mesh_stats(half)
        half.parent = pivot
        half.location = (0, -hinge_y, 0)
        for face in half.data.polygons:
            # Keep the section plane flat; softly shade the rounded skin.
            is_cut = all(abs(half.data.vertices[i].co.x) < 1e-6 for i in face.vertices)
            face.use_smooth = not is_cut
    pivot.rotation_euler.z = math.radians(angle)

for name, obj in layers:
    original = before[name]["volume"]
    combined = after["left"][name]["volume"] + after["right"][name]["volume"]
    error = abs(original - combined) / original
    assert error < 0.0001, (name, original, combined, error)
    assert before[name]["nonmanifold_edges"] == 0, (name, before[name])
    assert all(after[side][name]["nonmanifold_edges"] == 0 for side in after), (name, after)
    before[name]["relative_split_volume_error"] = error

layer_volume = sum(info["volume"] for info in before.values())
relative_layer_error = abs(layer_volume - whole_stats["volume"]) / whole_stats["volume"]
assert relative_layer_error < 0.0001, relative_layer_error

report = {
    "cut_plane": "x=0, vertical top-to-bottom",
    "half_rotations_degrees_about_vertical_z": {"left": -70, "right": 70},
    "pivot": "original rear edge of the cut plane, with a small outward spacing",
    "whole": whole_stats,
    "layers_before_cut": before,
    "halves_before_rotation": after,
    "relative_layer_volume_error": relative_layer_error,
    "interpretation": "Geometric model and static illustration, not production icon artwork or accessibility proof.",
}

# Remove the construction solids, leaving the intact fruit and the real cut pieces.
for obj in (outer, middle, core, skin_layer, rind_layer, flesh_layer, left_cutter, right_cutter):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 1400
scene.render.resolution_y = 760
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.render.use_stamp_filename = False  # Avoid embedding local paths in PNG metadata.
scene.render.filepath = "//cut-plus-geometry.png"
scene.world.color = (0, 0, 0)
scene.world.use_nodes = True
scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (0, 0, 0, 1)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "Medium High Contrast"
scene.view_settings.exposure = -0.35


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def area_light(name, loc, color, energy, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = color
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    aim(obj, (0, 0, 0))


area_light("Rose key", (-3, -5, 7), (1, 0.55, 0.75), 520, 6)
area_light("Cyan fill", (4, -4, 4), (0.45, 1, 0.95), 460, 5)
area_light("Violet rim", (0, 3, 5), (0.62, 0.25, 1), 600, 4)
camera_data = bpy.data.cameras.new("Camera")
camera = bpy.data.objects.new("Camera", camera_data)
bpy.context.collection.objects.link(camera)
camera.location = (0, -16, 3.6)
aim(camera, (0, 0, 0))
camera_data.type = "ORTHO"
camera_data.ortho_scale = 10.2
scene.camera = camera
bpy.context.view_layer.update()

# Check the actual cut-face normals, and that every visible mesh fits the frame.
to_camera = camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))
face_dots = {}
projected = []
for obj in [whole_display, *cut_halves]:
    if obj in cut_halves:
        dots = []
        for face in obj.data.polygons:
            if all(abs(obj.data.vertices[i].co.x) < 1e-6 for i in face.vertices):
                world_normal = obj.matrix_world.to_3x3() @ face.normal
                dots.append(world_normal.normalized().dot(to_camera))
        assert dots and min(dots) > 0.85, (obj.name, dots)
        face_dots[obj.name] = min(dots)
    for vertex in obj.data.vertices:
        projected.append(world_to_camera_view(scene, camera, obj.matrix_world @ vertex.co))

frame = {
    "min_x": min(v.x for v in projected), "max_x": max(v.x for v in projected),
    "min_y": min(v.y for v in projected), "max_y": max(v.y for v in projected),
}
assert frame["min_x"] > 0.02 and frame["max_x"] < 0.98, frame
assert frame["min_y"] > 0.02 and frame["max_y"] < 0.98, frame
assert min(v.z for v in projected) > 0, "A visible vertex is behind the camera"
report["minimum_cut_face_dot_toward_camera"] = face_dots
report["projected_frame_bounds"] = frame
(HERE / "geometry-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "cut-plus-geometry.blend"))
if os.environ.get("FRUIT_STUDY_SKIP_RENDER") != "1":
    bpy.ops.render.render(write_still=True)
print("CUT_STUDY_COMPLETE", json.dumps(report))
