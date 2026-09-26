import os
import bpy

def get_embedded_rig_path() -> str:
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    rig_path = os.path.join(addon_dir, "assets", "gorilla_rig.blend")
    if not os.path.exists(rig_path):
        raise FileNotFoundError(
            f"Embedded Gorilla Tag rig not found at expected path: {rig_path}.\n"
            "Please ensure the addon was installed with its assets folder intact."
        )
    return rig_path

def spawn_embedded_rig(recording_name: str):
    rig_blend_path = get_embedded_rig_path()

    scene = bpy.context.scene
    main_col = bpy.data.collections.get("MonkeFrames")
    if not main_col:
        main_col = bpy.data.collections.new("MonkeFrames")
        scene.collection.children.link(main_col)

    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in recording_name)
    col_name = f"Mocap_{safe_name}"

    counter = 1
    unique_col_name = col_name
    while bpy.data.collections.get(unique_col_name):
        unique_col_name = f"{col_name}_{counter}"
        counter += 1

    recording_col = bpy.data.collections.new(unique_col_name)
    main_col.children.link(recording_col)

    collections_to_import = ["Gorilla_IK_Rig", "gt_rig_bones"]
    imported_collections = []

    with bpy.data.libraries.load(rig_blend_path, link=False) as (data_from, data_to):
        data_to.collections = [c for c in collections_to_import if c in data_from.collections]

    for c in data_to.collections:
        if c:
            recording_col.children.link(c)
            imported_collections.append(c)

    armature_obj = None
    for c in imported_collections:
        for obj in c.objects:
            if obj.type == 'ARMATURE':
                armature_obj = obj
                break
        if armature_obj:
            break

    if not armature_obj:
        for obj in recording_col.all_objects:
            if obj.type == 'ARMATURE':
                armature_obj = obj
                break

    if not armature_obj:
        raise RuntimeError(
            f"Failed to locate armature in the appended rig from {rig_blend_path}."
        )

    armature_obj["MonkeFrames_Recording"] = unique_col_name
    recording_col["MonkeFrames_Armature"] = armature_obj.name

    return armature_obj, recording_col
