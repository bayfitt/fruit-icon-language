"""Build and render one fruit with genuinely curved front and back surfaces.

Run with: blender --background --factory-startup --python build_rounded_plus.py
The scene is static. Set FRUIT_STUDY_SKIP_RENDER=1 to run geometry checks only.
"""
import bpy
import bmesh
import json
import math
import os
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = Path(__file__).resolve().parent
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def fruit_material(name, dark, light, scale, bump_strength, emission=0.0, blossom=False,
                   subsurface=0.0, roughness=0.42, texture_name=None, texture_mix=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*light, 1)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = 0.22
    shader.inputs["Subsurface Weight"].default_value = subsurface
    shader.inputs["Emission Color"].default_value = (*dark, 1)
    shader.inputs["Emission Strength"].default_value = emission
    texcoord = nodes.new("ShaderNodeTexCoord")

    # Object coordinates stay tied to the uncut solid on both cut halves.
    color_noise = nodes.new("ShaderNodeTexNoise")
    color_noise.inputs["Scale"].default_value = 32 if name == "Violet fruit seeds" else 3.8
    color_noise.inputs["Detail"].default_value = 3
    links.new(texcoord.outputs["Object"], color_noise.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = 0.80
    ramp.color_ramp.elements[1].color = (*light, 1)
    links.new(color_noise.outputs["Fac"], ramp.inputs["Fac"])
    base_color = ramp.outputs["Color"]

    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    if blossom:
        # Fine organic pores without a regular cracked-tile pattern.
        pores = nodes.new("ShaderNodeTexNoise")
        pores.inputs["Scale"].default_value = 75
        pores.inputs["Detail"].default_value = 3
        links.new(texcoord.outputs["Object"], pores.inputs["Vector"])
        bump.inputs["Distance"].default_value = 0.018
        links.new(pores.outputs["Fac"], bump.inputs["Height"])
    else:
        fine_noise = nodes.new("ShaderNodeTexNoise")
        fine_noise.inputs["Scale"].default_value = scale
        fine_noise.inputs["Detail"].default_value = 3
        links.new(texcoord.outputs["Object"], fine_noise.inputs["Vector"])
        bump.inputs["Distance"].default_value = 0.035
        links.new(fine_noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])

    if texture_name:
        # Project original-fruit coordinates in three axes, so both cut halves
        # retain the same underlying natural texture rather than remapping it.
        source = HERE / "textures" / texture_name
        img = bpy.data.images.load(str(source), check_existing=True)
        img.pack()
        img.filepath = "//textures/" + texture_name
        mapping = nodes.new("ShaderNodeVectorMath")
        mapping.operation = "SCALE"
        mapping.inputs[3].default_value = 0.42 if texture_name == "flesh-albedo.png" else 0.35
        links.new(texcoord.outputs["Object"], mapping.inputs[0])
        image_node = nodes.new("ShaderNodeTexImage")
        image_node.image = img
        image_node.projection = "BOX"
        image_node.projection_blend = 0.35
        links.new(mapping.outputs["Vector"], image_node.inputs["Vector"])
        color_mix = nodes.new("ShaderNodeMixRGB")
        color_mix.blend_type = "MIX"
        color_mix.inputs[0].default_value = texture_mix
        links.new(base_color, color_mix.inputs[1])
        links.new(image_node.outputs["Color"], color_mix.inputs[2])
        base_color = color_mix.outputs["Color"]
        texture_bump = nodes.new("ShaderNodeBump")
        texture_bump.inputs["Strength"].default_value = 0.13 if blossom else 0.24
        texture_bump.inputs["Distance"].default_value = 0.012
        links.new(image_node.outputs["Color"], texture_bump.inputs["Height"])
        links.new(bump.outputs["Normal"], texture_bump.inputs["Normal"])
        links.new(texture_bump.outputs["Normal"], shader.inputs["Normal"])

    if blossom:
        # One small colored mark in original object coordinates, centered on the
        # cut plane. Each half inherits only its own half of the same mark.
        distance = nodes.new("ShaderNodeVectorMath")
        distance.operation = "DISTANCE"
        distance.inputs[1].default_value = (0.0, -0.25, -1.50)
        links.new(texcoord.outputs["Object"], distance.inputs[0])
        falloff = nodes.new("ShaderNodeMapRange")
        falloff.clamp = True
        falloff.inputs["From Min"].default_value = 0.025
        falloff.inputs["From Max"].default_value = 0.28
        falloff.inputs["To Min"].default_value = 0.90
        falloff.inputs["To Max"].default_value = 0.0
        links.new(distance.outputs["Value"], falloff.inputs["Value"])
        mix = nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MIX"
        mix.inputs[2].default_value = (0.48, 0.07, 0.0, 1)
        # Modulate the small mark into soft radial blossom folds.
        separate = nodes.new("ShaderNodeSeparateXYZ")
        links.new(texcoord.outputs["Object"], separate.inputs[0])
        offset_z = nodes.new("ShaderNodeMath")
        offset_z.operation = "ADD"
        offset_z.inputs[1].default_value = 1.50
        links.new(separate.outputs["Z"], offset_z.inputs[0])
        angle = nodes.new("ShaderNodeMath")
        angle.operation = "ARCTAN2"
        links.new(separate.outputs["X"], angle.inputs[0])
        links.new(offset_z.outputs[0], angle.inputs[1])
        repeat = nodes.new("ShaderNodeMath")
        repeat.operation = "MULTIPLY"
        repeat.inputs[1].default_value = 5.0
        links.new(angle.outputs[0], repeat.inputs[0])
        petal_wave = nodes.new("ShaderNodeMath")
        petal_wave.operation = "COSINE"
        links.new(repeat.outputs[0], petal_wave.inputs[0])
        petal_scale = nodes.new("ShaderNodeMapRange")
        petal_scale.inputs["From Min"].default_value = -1
        petal_scale.inputs["From Max"].default_value = 1
        petal_scale.inputs["To Min"].default_value = 0.35
        petal_scale.inputs["To Max"].default_value = 1.0
        links.new(petal_wave.outputs[0], petal_scale.inputs["Value"])
        petal_mask = nodes.new("ShaderNodeMath")
        petal_mask.operation = "MULTIPLY"
        links.new(falloff.outputs["Result"], petal_mask.inputs[0])
        links.new(petal_scale.outputs["Result"], petal_mask.inputs[1])
        links.new(petal_mask.outputs[0], mix.inputs[0])
        links.new(base_color, mix.inputs[1])
        links.new(mix.outputs["Color"], shader.inputs["Base Color"])
    else:
        links.new(base_color, shader.inputs["Base Color"])
    return mat


skin = fruit_material("Pink fruit skin", (0.48, 0.0, 0.13), (0.80, 0.0, 0.25), 22, 0.30, 0.20, True, 0.12, 0.35, "skin-albedo.png", 0.65)
rind = fruit_material("Lime rind", (0.48, 0.75, 0.0), (0.80, 1.0, 0.0), 24, 0.16, subsurface=0.06)
flesh = fruit_material("Turquoise flesh", (0.0, 0.08, 0.06), (0.0, 0.30, 0.22), 18, 0.22, subsurface=0.20, roughness=0.30, texture_name="flesh-albedo.png", texture_mix=0.30)
chamber_mat = fruit_material("Turquoise seed chamber", (0.0, 0.30, 0.23), (0.0, 0.55, 0.40), 24, 0.20, subsurface=0.20, roughness=0.30, texture_name="flesh-albedo.png", texture_mix=0.34)
pocket_mat = fruit_material("Soft tissue around seeds", (0.0, 0.40, 0.29), (0.0, 0.64, 0.46), 26, 0.16, subsurface=0.24, roughness=0.28, texture_name="flesh-albedo.png", texture_mix=0.28)
seed_mat = fruit_material("Violet fruit seeds", (0.14, 0.0, 0.22), (0.32, 0.0, 0.45), 30, 0.13, subsurface=0.06, roughness=0.24)
stem_mat = fruit_material("Green stem", (0.08, 0.30, 0.0), (0.25, 0.62, 0.0), 10, 0.15)


ANGLE_COUNT = 96
RING_COUNT = 24


def make_round_plus(name, arm, reach, full_depth, n_angle=ANGLE_COUNT, n_ring=RING_COUNT):
    """Star-shaped plus, with a single shared edge and convex front AND back."""
    verts = [(0, -full_depth / 2, 0), (0, full_depth / 2, 0)]
    faces = []
    front, back = [], []
    radii = []
    for i in range(n_angle):
        t = 2 * math.pi * i / n_angle
        c, s = math.cos(t), math.sin(t)
        # Smooth rounded-rectangle arms, with a soft maximum at their junction.
        exponent, blend = 6, 10
        rv = ((abs(c) / arm) ** exponent + (abs(s) / reach) ** exponent) ** (-1 / exponent)
        rh = ((abs(c) / reach) ** exponent + (abs(s) / arm) ** exponent) ** (-1 / exponent)
        radii.append((rv ** blend + rh ** blend) ** (1 / blend))

    for j in range(1, n_ring + 1):
        t = math.pi * j / (2 * n_ring)
        radial, half_depth = math.sin(t), full_depth * 0.5 * math.cos(t)
        fr, br = [], []
        for i in range(n_angle):
            angle = 2 * math.pi * i / n_angle
            x = radial * radii[i] * math.cos(angle)
            z = radial * radii[i] * math.sin(angle)
            if abs(x) < 1e-12:
                x = 0.0

            def vertex(y):
                # A shallow natural blossom-end dimple, centered on the cut.
                effect = math.exp(-((x / 0.16) ** 2 + (y / 0.18) ** 2))
                return (x, y, z + (0.035 * effect if z < -0.9 * reach else 0.0))

            fi = len(verts)
            verts.append(vertex(-half_depth))
            fr.append(fi)
            if j == n_ring:  # Exactly one perimeter ring shared by both sides.
                br.append(fi)
            else:
                bi = len(verts)
                verts.append(vertex(half_depth))
                br.append(bi)
        front.append(fr)
        back.append(br)

    for i in range(n_angle):
        nxt = (i + 1) % n_angle
        faces.append((0, front[0][i], front[0][nxt]))
        faces.append((1, back[0][nxt], back[0][i]))
        for j in range(n_ring - 1):
            faces.append((front[j][i], front[j + 1][i], front[j + 1][nxt], front[j][nxt]))
            faces.append((back[j][nxt], back[j + 1][nxt], back[j + 1][i], back[j][i]))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def duplicate(obj, name):
    other = obj.copy()
    other.data = obj.data.copy()
    other.name = name
    bpy.context.collection.objects.link(other)
    return other


def scaled_copy(obj, name, scale):
    copy = duplicate(obj, name)
    for v in copy.data.vertices:
        v.co *= scale
    copy.data.update()
    return copy


def boolean(obj, cutter, operation):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    mod = obj.modifiers.new(operation + " solid", "BOOLEAN")
    mod.operation = operation
    mod.solver = "EXACT"
    mod.object = cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)


def stats(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    data = {
        "volume": abs(bm.calc_volume(signed=True)) if bm.faces else 0.0,
        "nonmanifold_edges": sum(not e.is_manifold for e in bm.edges),
        "zero_area_faces": sum(f.calc_area() < 1e-12 for f in bm.faces),
        "faces": len(bm.faces),
    }
    bm.free()
    return data


def seed_components(obj):
    """Measure each disconnected cut seed in original-fruit coordinates."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bm.normal_update()
    remaining, found = set(bm.faces), []
    while remaining:
        stack, group = [remaining.pop()], []
        while stack:
            face = stack.pop()
            group.append(face)
            for edge in face.edges:
                for neighbor in edge.link_faces:
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        stack.append(neighbor)
        vertices = {v for f in group for v in f.verts}
        caps = [f for f in group if abs(f.normal.x) > 0.999 and
                all(abs(v.co.x) < 1e-6 for v in f.verts)]
        volume = abs(sum(f.verts[0].co.dot(f.verts[1].co.cross(f.verts[2].co)) / 6
                         for f in group))
        found.append({"z_min": min(v.co.z for v in vertices), "volume": volume,
                      "cap_area": sum(f.calc_area() for f in caps),
                      "cap_points": {(float(v.co.y), float(v.co.z)) for f in caps for v in f.verts}})
    bm.free()
    return sorted(found, key=lambda item: item["z_min"])


def point_set_distance(a, b):
    """Maximum bidirectional nearest-point distance between two cap meshes."""
    assert a and b
    def directed(p, q):
        return max(min(math.dist(x, y) for y in q) for x in p)
    return max(directed(a, b), directed(b, a))


def assert_inside(inner, outer, label):
    remainder = duplicate(inner, label + " containment remainder")
    boolean(remainder, outer, "DIFFERENCE")
    remainder_stats = stats(remainder)
    bpy.data.objects.remove(remainder, do_unlink=True)
    assert remainder_stats["volume"] < 1e-6, (label, remainder_stats)
    return remainder_stats["volume"]


def ellipsoid(name, center, radii, taper=0.0, lean=0.0):
    """Make one closed, transformed ellipsoid in original-fruit coordinates."""
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=center)
    obj = bpy.context.object
    obj.name = name
    for vertex in obj.data.vertices:
        # A gentle taper makes seeds more almond-like than identical beads.
        f = 1.0 - taper * (vertex.co.z + 1.0) / 2.0
        vertex.co.x *= f
        vertex.co.y *= f
    obj.scale = radii
    obj.rotation_euler.x = math.radians(lean)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def join_volumes(objects, name):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    combined = bpy.context.object
    combined.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    combined.select_set(False)
    return combined


def make_seed_structure():
    """A central chamber and three non-overlapping, varied seeds.

    All seed solids cross the cut plane.  Their opposite halves are produced
    by the same Boolean cut as the rest of the fruit, not painted on later.
    """
    # A slight offset avoids aligning UV-sphere poles exactly with the cut plane.
    center_x = 0.012
    chamber = ellipsoid("Seed chamber volume", (center_x, 0, 0), (0.19, 0.27, 0.75))
    # Real fruit chambers are not perfectly even concentric ellipses.
    for vertex in chamber.data.vertices:
        t = vertex.co.z / 0.75
        vertex.co.x *= 1.0 + 0.12 * t + 0.04 * math.sin(4 * t)
        vertex.co.y *= 1.0 + 0.12 * t + 0.04 * math.sin(4 * t)
        vertex.co.y += 0.025 * math.sin(3 * t) * (1 - min(abs(t), 1))
    chamber.data.update()
    # Keep all layer mesh coordinates in the same original-fruit frame.
    bpy.context.view_layer.objects.active = chamber
    chamber.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    chamber.select_set(False)
    specifications = [
        (-0.39, -0.035, 0.075, 0.080, 0.140, -14),
        (0.00, 0.040, 0.085, 0.090, 0.160, 16),
        (0.39, -0.035, 0.070, 0.075, 0.130, -11),
    ]
    objects, pockets, recorded = [], [], []
    for i, (z, y, rx, ry, rz, lean) in enumerate(specifications, 1):
        seed = ellipsoid("Seed %d" % i, (center_x, y, z), (rx, ry, rz), taper=0.28, lean=lean)
        pocket = ellipsoid("Seed pocket %d" % i, (center_x, y, z),
                           (rx * 1.14, ry * 1.14, rz * 1.14), taper=0.24, lean=lean)
        assert_inside(seed, pocket, "seed pocket %d" % i)
        info = stats(seed)
        x_values = [v.co.x + seed.location.x for v in seed.data.vertices]
        assert info["volume"] > 0 and info["nonmanifold_edges"] == 0 and info["zero_area_faces"] == 0, info
        assert min(x_values) < -0.001 and max(x_values) > 0.001, (i, min(x_values), max(x_values))
        recorded.append({"name": seed.name, "center_x": center_x, "center_y": y, "center_z": z,
                         "radii": [rx, ry, rz], "lean_degrees": lean,
                         "crosses_cut_plane": True, "mesh": info})
        objects.append(seed)
        pockets.append(pocket)
    # The z extents are separated, so these three closed seeds do not overlap.
    ranges = [(s[0] - 1.1 * 1.14 * s[4], s[0] + 1.1 * 1.14 * s[4]) for s in specifications]
    assert all(ranges[i][1] < ranges[i + 1][0] for i in range(len(ranges) - 1)), ranges
    return chamber, join_volumes(pockets, "Three seed pocket volumes"), join_volumes(objects, "Three original seed volumes"), recorded


outer_depth = 1.44
outer = make_round_plus("One whole fruit", 0.62, 1.60, outer_depth)
middle = scaled_copy(outer, "Inside of skin", 0.90)
core = scaled_copy(outer, "Inside of rind", 0.77)
# Slightly irregular inner rind boundary while keeping the outer plus intact.
for vertex in core.data.vertices:
    t = vertex.co.z / (1.60 * 0.77)
    variation = 1.0 + 0.080 * math.sin(5.3 * t) + 0.030 * math.sin(11 * t)
    vertex.co.x *= variation
    vertex.co.y *= variation
core.data.update()
# Triangulate once after warping so every later Boolean uses the same surface.
core_bmesh = bmesh.new()
core_bmesh.from_mesh(core.data)
bmesh.ops.triangulate(core_bmesh, faces=list(core_bmesh.faces))
core_bmesh.to_mesh(core.data)
core_bmesh.free()
core.data.update()
chamber, pocket_solids, seed_solids, seed_records = make_seed_structure()
whole_stats = stats(outer)
assert whole_stats["nonmanifold_edges"] == whole_stats["zero_area_faces"] == 0, whole_stats
assert whole_stats["volume"] > 0
containment = {
    "rind_outside_skin_volume": assert_inside(middle, outer, "rind"),
    "flesh_outside_rind_volume": assert_inside(core, middle, "flesh"),
    "chamber_outside_flesh_volume": assert_inside(chamber, core, "seed chamber"),
    "pockets_outside_chamber_volume": assert_inside(pocket_solids, chamber, "seed pockets"),
    "seeds_outside_pockets_volume": assert_inside(seed_solids, pocket_solids, "seeds"),
}

# The front/back bulges are mesh geometry, not a lighting effect.
front_pole_y = outer.data.vertices[0].co.y
back_pole_y = outer.data.vertices[1].co.y
quarter_index = (RING_COUNT // 4 - 1) * ANGLE_COUNT
half_index = (RING_COUNT // 2 - 1) * ANGLE_COUNT
quarter = outer.data.vertices[2 + 2 * quarter_index].co.y
half = outer.data.vertices[2 + 2 * half_index].co.y
back_quarter = outer.data.vertices[3 + 2 * quarter_index].co.y
back_half = outer.data.vertices[3 + 2 * half_index].co.y
edge = outer.data.vertices[-1].co.y
assert front_pole_y < quarter < half < -1e-5
assert back_pole_y > back_quarter > back_half > 1e-5 and abs(edge) < 1e-6
profile = {"front_center_y": front_pole_y, "back_center_y": back_pole_y,
           "front_sample_quarter_y": quarter, "front_sample_half_y": half,
           "back_sample_quarter_y": back_quarter, "back_sample_half_y": back_half,
           "shared_perimeter_y": edge}

# One short stem is on the left of the central cut; its base overlaps the fruit.
curve = bpy.data.curves.new("Single curved stem shape", "CURVE")
curve.dimensions = "3D"
curve.resolution_u = 16
curve.bevel_depth = 0.075
curve.bevel_resolution = 4
curve.use_fill_caps = True
spline = curve.splines.new("BEZIER")
spline.bezier_points.add(3)
for p, coords, radius in zip(spline.bezier_points,
                              [(-0.18, 0, 1.49), (-0.17, 0, 1.60),
                               (-0.15, 0, 1.72), (-0.11, 0, 1.84)],
                              [1.10, 1.0, 0.78, 0.52]):
    p.co, p.radius = coords, radius
    p.handle_left_type = p.handle_right_type = "AUTO"
stem = bpy.data.objects.new("One offset stem", curve)
bpy.context.collection.objects.link(stem)
curve.materials.append(stem_mat)
bpy.context.view_layer.objects.active = stem
stem.select_set(True)
bpy.ops.object.convert(target="MESH")
stem = bpy.context.object
stem.select_set(False)
# Curve conversion can leave coincident, unwelded cap loops at both ends.
stem_bmesh = bmesh.new()
stem_bmesh.from_mesh(stem.data)
bmesh.ops.remove_doubles(stem_bmesh, verts=list(stem_bmesh.verts), dist=1e-6)
bmesh.ops.recalc_face_normals(stem_bmesh, faces=stem_bmesh.faces)
stem_bmesh.to_mesh(stem.data)
stem_bmesh.free()
stem.data.update()
stem_stats = stats(stem)
assert stem_stats["nonmanifold_edges"] == 0 and stem_stats["zero_area_faces"] == 0, stem_stats
assert max(v.co.x for v in stem.data.vertices) < -0.005
assert min(v.co.z for v in stem.data.vertices) < 1.55  # base penetrates the fruit
for poly in stem.data.polygons:
    poly.use_smooth = True


def whole_view(name, x, angle=0):
    parent = bpy.data.objects.new(name + " orientation", None)
    bpy.context.collection.objects.link(parent)
    parent.location.x = x
    parent.rotation_euler.z = math.radians(angle)
    body = duplicate(outer, name + " fruit")
    body.data.materials.clear()
    body.data.materials.append(skin)
    body.parent = parent
    view_stem = duplicate(stem, name + " stem")
    view_stem.parent = parent
    return body, view_stem


front_body, front_stem = whole_view("Front", -4.40)
side_body, side_stem = whole_view("Side", -1.30, 75)

skin_layer = duplicate(outer, "Skin before cut")
boolean(skin_layer, middle, "DIFFERENCE")
skin_layer.data.materials.clear()
skin_layer.data.materials.append(skin)
# Verify actual stem contact with the fruit skin, not just matching height.
stem_contact_mesh = duplicate(stem, "Stem contact check")
boolean(stem_contact_mesh, skin_layer, "INTERSECT")
stem_contact_volume = stats(stem_contact_mesh)["volume"]
bpy.data.objects.remove(stem_contact_mesh, do_unlink=True)
assert stem_contact_volume > 1e-6, stem_contact_volume
rind_layer = duplicate(middle, "Rind before cut")
boolean(rind_layer, core, "DIFFERENCE")
rind_layer.data.materials.clear()
rind_layer.data.materials.append(rind)
flesh_layer = duplicate(core, "Flesh before cut")
boolean(flesh_layer, chamber, "DIFFERENCE")
flesh_layer.data.materials.clear()
flesh_layer.data.materials.append(flesh)
chamber_layer = duplicate(chamber, "Seed chamber before cut")
boolean(chamber_layer, pocket_solids, "DIFFERENCE")
chamber_layer.data.materials.clear()
chamber_layer.data.materials.append(chamber_mat)
pocket_layer = duplicate(pocket_solids, "Seed pockets before cut")
boolean(pocket_layer, seed_solids, "DIFFERENCE")
pocket_layer.data.materials.clear()
pocket_layer.data.materials.append(pocket_mat)
seeds_layer = duplicate(seed_solids, "Seeds before cut")
seeds_layer.data.materials.clear()
seeds_layer.data.materials.append(seed_mat)
layers = [("skin", skin_layer), ("rind", rind_layer), ("flesh", flesh_layer),
          ("chamber", chamber_layer), ("pockets", pocket_layer), ("seeds", seeds_layer)]
before = {name: stats(obj) for name, obj in layers}


def halfspace(name, start, end):
    bpy.ops.mesh.primitive_cube_add(size=2, location=((start + end) / 2, 0, 0))
    cube = bpy.context.object
    cube.name = name
    cube.dimensions = (end - start, 10, 10)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return cube


left_cutter = halfspace("Left x <= 0", -5, 0)
right_cutter = halfspace("Right x >= 0", 0, 5)
after, pieces, seed_pieces = {"left": {}, "right": {}}, [], {}
hinge_y = outer_depth / 2
left_stem = None
for side, cutter, angle in (("left", left_cutter, -70), ("right", right_cutter, 70)):
    pivot = bpy.data.objects.new(side.title() + " rotation", None)
    bpy.context.collection.objects.link(pivot)
    pivot.location = (2.85 + (-0.10 if side == "left" else 0.10), hinge_y, 0)
    for name, layer in layers:
        piece = duplicate(layer, side.title() + " " + name)
        boolean(piece, cutter, "INTERSECT")
        after[side][name] = stats(piece)
        if name == "seeds":
            seed_pieces[side] = piece
        piece.parent = pivot
        piece.location = (0, -hinge_y, 0)
        for poly in piece.data.polygons:
            is_cut_face = (abs(poly.normal.x) > 0.999 and
                           all(abs(piece.data.vertices[i].co.x) < 1e-6 for i in poly.vertices))
            poly.use_smooth = not is_cut_face
        pieces.append(piece)
    if side == "left":
        left_stem = duplicate(stem, "Left half stem")
        left_stem.parent = pivot
        left_stem.location = (0, -hinge_y, 0)
    pivot.rotation_euler.z = math.radians(angle)

for name, layer in layers:
    original = before[name]["volume"]
    combined = after["left"][name]["volume"] + after["right"][name]["volume"]
    error = abs(original - combined) / original
    assert error < 1e-4, (name, error)
    assert before[name]["nonmanifold_edges"] == 0 and before[name]["zero_area_faces"] == 0, (name, before[name])
    assert all(after[side][name]["nonmanifold_edges"] == 0 and
               after[side][name]["zero_area_faces"] == 0 for side in after), (name, after)
    before[name]["relative_split_volume_error"] = error

layer_volume = sum(v["volume"] for v in before.values())
layer_error = abs(layer_volume - whole_stats["volume"]) / whole_stats["volume"]
assert layer_error < 1e-5, layer_error

left_seeds, right_seeds = seed_components(seed_pieces["left"]), seed_components(seed_pieces["right"])
assert len(left_seeds) == len(right_seeds) == len(seed_records) == 3
seed_pairs = []
for record, left, right in zip(sorted(seed_records, key=lambda r: r["center_z"]), left_seeds, right_seeds):
    assert left["cap_area"] > 0 and right["cap_area"] > 0
    assert math.isclose(left["cap_area"], right["cap_area"], rel_tol=1e-5, abs_tol=1e-8)
    combined_volume = left["volume"] + right["volume"]
    assert math.isclose(combined_volume, record["mesh"]["volume"], rel_tol=1e-4, abs_tol=1e-9)
    cap_error = point_set_distance(left["cap_points"], right["cap_points"])
    assert cap_error < 1e-6, (record["name"], cap_error)
    seed_pairs.append({"name": record["name"], "left_cap_area": left["cap_area"],
                       "right_cap_area": right["cap_area"],
                       "left_volume": left["volume"], "right_volume": right["volume"],
                       "max_corresponding_cap_point_distance": cap_error})

report = {
    "description": "One modeled plus-shaped fruit with curved front and back, an offset stem, a blossom mark, and a central chamber of three seeds.",
    "cut_plane": "x=0, vertical top-to-bottom",
    "half_rotations_degrees_about_vertical_z": {"left": -70, "right": 70},
    "front_and_back_profile": profile,
    "whole_fruit": whole_stats,
    "nested_containment": containment,
    "original_seeds": seed_records,
    "matched_seed_sections": seed_pairs,
    "layers_before_cut": before,
    "halves_before_rotation": after,
    "relative_layer_volume_error": layer_error,
    "stem": {"description": "One separate curved stem mesh intersects the skin and lies entirely on the left side of the cut; the meshes are not boolean-unioned.",
             "intersection_with_skin_volume": stem_contact_volume, "mesh": stem_stats},
    "blossom_mark": "One centered material mark in original-object coordinates is divided by the cut.",
    "limitations": "Static geometry study, not finalized icon artwork or proof of small-size accessibility.",
}

for obj in (outer, middle, core, chamber, pocket_solids, seed_solids, stem, skin_layer, rind_layer,
            flesh_layer, chamber_layer, pocket_layer, seeds_layer, left_cutter, right_cutter):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 1700
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.render.use_stamp_filename = False
scene.render.filepath = "//rounded-plus-study.png"
scene.world.use_nodes = True
scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (0, 0, 0, 1)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "Medium High Contrast"
scene.view_settings.exposure = -0.35


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def area_light(name, location, color, energy, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.color, data.size = energy, color, size
    data.shape = "DISK"
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    aim(obj, (-0.6, 0, 0))


area_light("Rose key", (-4, -5, 7), (1, 0.55, 0.75), 620, 7)
area_light("Cyan fill", (4, -4, 4), (0.45, 1, 0.95), 480, 6)
area_light("Violet rim", (0, 3, 5), (0.62, 0.25, 1), 640, 5)
area_light("Left fill", (-8, -3, 0), (1, 0.30, 0.62), 350, 6)
area_light("Right fill", (8, -3, 0), (1, 0.30, 0.62), 350, 6)
area_light("Soft underside fill", (-3, -4, -5), (1, 0.30, 0.48), 260, 6)
camera_data = bpy.data.cameras.new("Camera")
camera = bpy.data.objects.new("Camera", camera_data)
bpy.context.collection.objects.link(camera)
camera.location = (-0.7, -18, -1.8)
aim(camera, (-0.7, 0, 0))
camera_data.type = "ORTHO"
camera_data.ortho_scale = 11.8
scene.camera = camera
bpy.context.view_layer.update()

visible = [front_body, front_stem, side_body, side_stem, *pieces, left_stem]
projected, face_dots = [], {}
to_camera = camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))
for obj in visible:
    if obj in pieces:
        dots = []
        for face in obj.data.polygons:
            if (abs(face.normal.x) > 0.999 and
                    all(abs(obj.data.vertices[i].co.x) < 1e-6 for i in face.vertices)):
                n = (obj.matrix_world.to_3x3() @ face.normal).normalized()
                dots.append(n.dot(to_camera))
        assert dots and min(dots) > 0.85, (obj.name, dots)
        face_dots[obj.name] = min(dots)
    projected.extend(world_to_camera_view(scene, camera, obj.matrix_world @ v.co) for v in obj.data.vertices)
frame = {"min_x": min(v.x for v in projected), "max_x": max(v.x for v in projected),
         "min_y": min(v.y for v in projected), "max_y": max(v.y for v in projected)}
assert frame["min_x"] > 0.02 and frame["max_x"] < 0.98, frame
assert frame["min_y"] > 0.02 and frame["max_y"] < 0.98, frame
assert min(v.z for v in projected) > 0
report["minimum_cut_face_dot_toward_camera"] = face_dots
report["projected_frame_bounds"] = frame
(HERE / "geometry-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "rounded-plus-study.blend"))
if os.environ.get("FRUIT_STUDY_SKIP_RENDER") != "1":
    bpy.ops.render.render(write_still=True)
print("ROUNDED_FRUIT_COMPLETE", json.dumps(report))
