import json
import os
import numpy as np
import trimesh
import shapely.geometry

import shutil
from pathlib import Path
# ------------------------------------------------------------------------------


def load_osm_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

# ------------------------------------------------------------------------------


def build_node_index(nodes):
    """Create a dict: node_id -> node with x,y coordinates."""
    return {node['id']: node for node in nodes}

# ------------------------------------------------------------------------------


def extract_polygon_from_way(node_ids, node_index):
    """Return list of (x,y) tuples for the way's nodes."""
    polygon = []
    for nid in node_ids:
        node = node_index.get(nid)
        if node and 'x' in node and 'y' in node:
            polygon.append((node['x'], node['y']))
    return polygon

# ------------------------------------------------------------------------------


def get_building_height(tags, default_floor_height=3.0, min_height=3.0):
    """Compute building height using tags."""
    if not tags:
        return min_height
    if 'height' in tags:
        try:
            return float(tags['height'])
        except ValueError:
            pass
    if 'building:levels' in tags:
        try:
            return float(tags['building:levels']) * default_floor_height
        except ValueError:
            pass
    return min_height

# ------------------------------------------------------------------------------


def extrude_polygon_to_watertight_mesh(polygon, height=10.0):
    """
    Use trimesh with shapely to extrude a 2D polygon into a watertight 3D mesh volume.
    """
    if len(polygon) < 3:
        return None

    polygon_2d = np.array(polygon)

    # Create shapely polygon, try to fix invalid polygons
    poly_shape = shapely.geometry.Polygon(polygon_2d)
    if not poly_shape.is_valid:
        poly_shape = poly_shape.buffer(0)

    if not poly_shape.is_valid or poly_shape.is_empty:
        print("Invalid polygon, skipping extrusion.")
        return None

    # Create trimesh path from shapely polygon
    path = trimesh.load_path(poly_shape)

    # Extrude to get solid mesh
    solid = path.extrude(height)

    # Repair if needed
    if not solid.is_watertight:
        solid = solid.fill_holes()

    if not solid.is_watertight:
        print("Warning: mesh extrusion resulted in a non-watertight mesh.")

    return solid

# ------------------------------------------------------------------------------


def normalize_mesh(mesh_obj, min_coords=(0, 0, 0)):
    """
    Translate mesh to origin based on min_coords and lift slightly above Z=0.
    """
    translation = -np.array(min_coords)
    mesh_obj.apply_translation(translation)
    return mesh_obj

# ------------------------------------------------------------------------------


def create_box_stl(filename,
                   x_len, y_len, z_len,
                   xy_offset=0.0, z_offset=0.0):
    """
    Create a simple box mesh and save as STL for bounding box visualization.
    x_len, y_len, z_len: dimensions of the box.
    xy_offset: offset in X and Y at the edges --> padding.
    z_offset: offset in Z above highest building.
    """
    box = trimesh.creation.box(extents=[x_len+2*xy_offset, y_len+2*xy_offset,
                                        z_len+z_offset])
    box.apply_translation([x_len/2.0,
                           y_len/2.0,
                           z_len/2.0+z_offset/2.0])  # Lift the box above Z=0
    box.export(filename)
    print(f"Box STL saved as '{filename}'.")


def create_box_stl_xoff(filename,
                        x_len, y_len, z_len,
                        x0_offset=0.0, x1_offset=0.0,
                        y_offset=0.0,
                        z_offset=0.0):
    """
    Create a simple box mesh and save as STL for bounding box visualization.

    Parameters:
    -----------
    x_len, y_len, z_len : float
        Base dimensions of the box (before padding).
    x0_offset : float
        Padding on the negative X side (left).
    x1_offset : float
        Padding on the positive X side (right).
    y_offset : float
        Symmetric padding in Y direction (both sides).
    z_offset : float
        Offset in Z above highest building.
    """
    total_x = x_len + x0_offset + x1_offset
    total_y = y_len + 2*y_offset
    total_z = z_len + z_offset

    box = trimesh.creation.box(extents=[total_x, total_y, total_z])

    x_center = x_len/2.0 + (x1_offset - x0_offset)/2.0
    y_center = y_len/2.0
    z_center = z_len/2.0 + z_offset/2.0

    box.apply_translation([x_center, y_center, z_center])
    box.export(filename)
    print(f"Box STL saved as '{filename}'.")


def create_cylinder_stl_1(filename,
                        x_len, y_len, z_len,
                        r_offset=0.0,
                        z_offset=0.0,
                        sections=512):
    """
    Create a vertical cylinder (axis along Z) centered on the building cluster
    footprint, and save as STL.

    The cylinder radius is set to half the diagonal of the XY bounding box plus
    r_offset, so it fully contains all buildings regardless of orientation.

    Parameters:
    -----------
    x_len, y_len, z_len : float
        Bounding box dimensions of the (already-normalised) buildings.
    r_offset : float
        Extra radial padding beyond the minimum enclosing radius.
    z_offset : float
        Extra height above the tallest building.
    sections : int
        Number of facets around the cylinder circumference (higher = smoother).
    """
    # Minimum enclosing radius of the XY footprint + padding
    radius = 0.5 * np.sqrt(x_len**2 + y_len**2) + r_offset
    total_z = z_len + z_offset

    # trimesh creates a cylinder centred at the origin with axis along Z
    cyl = trimesh.creation.cylinder(radius=radius,
                                    height=total_z,
                                    sections=sections)

    # Translate so the base sits at Z=0 and the XY centre aligns with the
    # building cluster centre
    cyl.apply_translation([x_len / 2.0,
                           y_len / 2.0,
                           total_z / 2.0])

    cyl.export(filename)
    print(f"Cylinder STL saved as '{filename}'.")
    print(f"  radius = {radius:.2f} m  (diagonal/2 + r_offset={r_offset})")
    print(f"  height = {total_z:.2f} m  (z_len + z_offset={z_offset})")


def create_cylinder_stl(filename,
                        x_len, y_len, z_len,
                        r_offset=0.0,
                        z_offset=0.0,
                        sections=128,
                        radial_rings=512):
    """
    Cylinder with a properly stitched watertight mesh.
    Cap outer-ring vertices are shared with the lateral surface,
    so no vertex-merging is needed and the mesh is guaranteed watertight.
    """
    radius  = 0.5 * np.sqrt(x_len**2 + y_len**2) + r_offset
    total_z = z_len + z_offset
    cx, cy  = x_len / 2.0, y_len / 2.0

    thetas = np.linspace(0, 2 * np.pi, sections, endpoint=False)
    radii  = np.linspace(0, radius, radial_rings + 1)  # r=0 … r=radius

    # ------------------------------------------------------------------
    # Vertex layout (same for bottom and top caps)
    #   idx 0                              → centre
    #   idx 1 + (ring-1)*sections + s      → ring ∈ [1..radial_rings], s ∈ [0..sections)
    # ------------------------------------------------------------------
    def ring_start(ring):
        return 0 if ring == 0 else 1 + (ring - 1) * sections

    def cap_xy():
        """Return (N,2) XY coords for one cap, centre first then ring-by-ring."""
        pts = [[0.0, 0.0]]
        for r in radii[1:]:
            pts.extend([[r * np.cos(t), r * np.sin(t)] for t in thetas])
        return np.array(pts)

    xy = cap_xy()           # shared XY pattern
    n_cap = len(xy)         # 1 + radial_rings * sections

    # Full vertex array: bottom cap, then top cap  (NO separate side verts)
    bot_xyz = np.column_stack([xy, np.zeros(n_cap)])
    top_xyz = np.column_stack([xy, np.full(n_cap, total_z)])
    verts   = np.vstack([bot_xyz, top_xyz])   # shape (2*n_cap, 3)

    # Top cap indices are offset by n_cap
    def bi(ring, s):   return ring_start(ring) + s % sections          # bottom
    def ti(ring, s):   return n_cap + ring_start(ring) + s % sections  # top

    faces = []

    # --- Bottom cap (normal = -Z → clockwise winding when viewed from below) ---
    for s in range(sections):
        faces.append([0, bi(1, s+1), bi(1, s)])          # inner fan
    for ring in range(1, radial_rings):
        for s in range(sections):
            a0, a1 = bi(ring,   s), bi(ring,   s+1)
            b0, b1 = bi(ring+1, s), bi(ring+1, s+1)
            faces.append([a0, a1, b0])
            faces.append([a1, b1, b0])

    # --- Top cap (normal = +Z → counter-clockwise winding viewed from above) ---
    for s in range(sections):
        faces.append([n_cap, ti(1, s), ti(1, s+1)])      # inner fan
    for ring in range(1, radial_rings):
        for s in range(sections):
            a0, a1 = ti(ring,   s), ti(ring,   s+1)
            b0, b1 = ti(ring+1, s), ti(ring+1, s+1)
            faces.append([a0, b0, a1])
            faces.append([a1, b0, b1])

    # --- Lateral surface: reuses outer-ring verts from both caps ---
    outer = radial_rings
    for s in range(sections):
        b0, b1 = bi(outer, s), bi(outer, s+1)
        t0, t1 = ti(outer, s), ti(outer, s+1)
        faces.append([b0, b1, t0])
        faces.append([b1, t1, t0])

    # ------------------------------------------------------------------
    mesh = trimesh.Trimesh(vertices=verts,
                           faces=np.array(faces),
                           process=False)   # no merging needed — verts are already shared

    if not mesh.is_watertight:
        print("  Warning: mesh is not watertight.")
    if not mesh.is_volume:
        print("  Warning: mesh volume check failed.")

    mesh.apply_translation([cx, cy, 0.0])
    mesh.export(filename)

    print(f"Cylinder STL saved as '{filename}'.")
    print(f"  radius        = {radius:.3f} m")
    print(f"  height        = {total_z:.3f} m")
    print(f"  sections      = {sections},  cap rings = {radial_rings}")
    print(f"  total verts   = {len(verts)},  total faces = {len(faces)}")

# ------------------------------------------------------------------------------


def json2stls(input_json: str, output_stl_name: str,
              x_offsets: tuple[int, int], y_offset: int, z_offset: int,
              export_buildings: bool = False,
              domain: str = 'box'):
    """
    Parameters
    ----------
    domain : {'box', 'cylinder'}
        Shape of the outer flow domain.
        - 'box'      : rectangular domain, same behaviour as before.
        - 'cylinder' : circular domain. x_offsets[0] is used as the radial
                       padding (r_offset); x_offsets[1] is ignored.
    """

    output_stl = output_stl_name + '.stl'

    data = load_osm_json(input_json)
    nodes = data.get('nodes', [])
    buildings = data.get('buildings', [])

    node_index = build_node_index(nodes)
    all_meshes = []

    print("Processing buildings to create watertight meshes...")

    for bld in buildings:
        tags = bld.get('tags', {})
        height = get_building_height(tags)

        mesh_obj = None
        if bld['type'] == 'way' and 'nodes' in bld:
            polygon = extract_polygon_from_way(bld['nodes'], node_index)
            if len(polygon) < 3:
                continue
            mesh_obj = extrude_polygon_to_watertight_mesh(
                polygon, height=height)

        elif bld['type'] == 'relation' and 'members' in bld:
            continue

        if mesh_obj:
            all_meshes.append(mesh_obj)

    assert all_meshes, "No building geometry found to write."

    combined = trimesh.util.concatenate(all_meshes)
    bbox_min, bbox_max = combined.bounds

    # Normalize combined mesh to origin
    combined = normalize_mesh(combined, min_coords=bbox_min)
    combined.export(output_stl)
    print(f"Saved combined watertight STL file as {output_stl}")

    bbox_size = bbox_max - bbox_min
    print(f"Bounding box min: {bbox_min}, max: {bbox_max}")
    print(f"Bounding box size (dx, dy, dz): {bbox_size}")

    # Create outer domain STL
    domain_filename = f"box_{output_stl_name}.stl"

    if domain == 'cylinder':
        r_offset = x_offsets[0]   # reuse first offset as radial padding
        create_cylinder_stl(domain_filename,
                            *bbox_size,
                            r_offset=r_offset,
                            z_offset=z_offset)
    else:
        create_box_stl_xoff(domain_filename,
                            *bbox_size,
                            x0_offset=x_offsets[0], x1_offset=x_offsets[1],
                            y_offset=y_offset,
                            z_offset=z_offset)

    if export_buildings:

        path = Path("buildings")
        if path.exists():
            shutil.rmtree(path)
        os.makedirs("buildings", exist_ok=True)
        building_counter = 1

        for bld in buildings:
            tags = bld.get('tags', {})
            height = get_building_height(tags)

            mesh_obj = None
            if bld['type'] == 'way' and 'nodes' in bld:
                polygon = extract_polygon_from_way(bld['nodes'], node_index)
                if len(polygon) < 3:
                    continue
                mesh_obj = extrude_polygon_to_watertight_mesh(
                    polygon, height=height)

            elif bld['type'] == 'relation' and 'members' in bld:
                continue

            if mesh_obj:
                mesh_obj = normalize_mesh(mesh_obj, min_coords=bbox_min)
                filename = f"building_{building_counter:07d}.stl"
                filepath = os.path.join("buildings", filename)
                mesh_obj.export(filepath)
                print(f"Saved individual building STL: {filename}")
                building_counter += 1

        if building_counter == 1:
            print("No individual building meshes were created.")
        else:
            print(
                f"Saved {building_counter - 1} individual watertight building STL files.")

    print("Done.")
