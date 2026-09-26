import json
import math
import os
import bpy
import mathutils

from . import coordinator
from . import rig_spawner

class MocapImportError(Exception):
    pass

def parse_and_validate_mfmc(file_path: str) -> dict:
    if not os.path.exists(file_path):
        raise MocapImportError(f"Mocap file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as ex:
        raise MocapImportError(f"Corrupted or invalid JSON in .mfmc file: {ex}")

    format_name = data.get("format")
    if format_name != "MonkeFrames Mocap":
        raise MocapImportError(
            f"Invalid file format '{format_name}'. Expected 'MonkeFrames Mocap'."
        )

    version = data.get("formatVersion", 1)
    if version > 1:
        raise MocapImportError(
            f"Unsupported format version {version}. This addon supports version 1."
        )

    frames = data.get("frames")
    if not frames or not isinstance(frames, list):
        raise MocapImportError("The mocap file contains no recording frames.")

    return data

def import_mocap_file(file_path: str, context=None) -> dict:
    if context is None:
        context = bpy.context

    data = parse_and_validate_mfmc(file_path)

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    sample_rate = float(data.get("sampleRate", 24.0))
    frames = data.get("frames", [])
    frame_count = len(frames)
    duration = float(data.get("duration", frame_count / sample_rate))
    metadata = data.get("metadata", {})
    player_name = metadata.get("playerName", "Gorilla")

    armature_obj, recording_col = rig_spawner.spawn_embedded_rig(base_name)

    if context.object and context.object.mode != 'OBJECT':
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

    try:
        bpy.ops.object.select_all(action='DESELECT')
    except Exception:
        pass

    context.view_layer.objects.active = armature_obj
    armature_obj.select_set(True)

    try:
        bpy.ops.object.mode_set(mode='POSE')
    except Exception as ex:
        print(f"[MonkeFrames] Warning: Failed to enter POSE mode: {ex}")

    scene = context.scene
    scene.render.fps = max(1, round(sample_rate))
    scene.render.fps_base = 1.0
    scene.frame_start = 1
    scene.frame_end = max(1, frame_count)
    scene.frame_current = 1

    if not armature_obj.animation_data:
        armature_obj.animation_data_create()

    action_name = f"Action_{recording_col.name}"
    action = bpy.data.actions.new(name=action_name)
    armature_obj.animation_data.action = action

    pose = armature_obj.pose
    pb_root = pose.bones.get("root.001")
    pb_head = pose.bones.get("head")
    pb_lh = pose.bones.get("hand_controller.L")
    pb_rh = pose.bones.get("hand_controller.R")

    pb_l_index = pose.bones.get("index_control.L")
    pb_l_middle = pose.bones.get("middle_control.L")
    pb_l_thumb = pose.bones.get("thumb_control.L")

    pb_r_index = pose.bones.get("index_control.R")
    pb_r_middle = pose.bones.get("middle_control.R")
    pb_r_thumb = pose.bones.get("thumb_control.R")

    finger_controls = [pb_l_index, pb_l_middle, pb_l_thumb, pb_r_index, pb_r_middle, pb_r_thumb]
    for pb in finger_controls:
        if pb:
            pb.rotation_mode = 'XYZ'

    if pb_root: pb_root.rotation_mode = 'XYZ'
    if pb_head: pb_head.rotation_mode = 'XYZ'
    if pb_lh: pb_lh.rotation_mode = 'XYZ'
    if pb_rh: pb_rh.rotation_mode = 'XYZ'

    rad_75 = math.radians(75.0)
    rad_65 = math.radians(65.0)
    b_head_mat = pb_head.bone.matrix_local.to_3x3().to_4x4() if pb_head else None

    for i, frame in enumerate(frames):
        blender_frame = 1 + i

        body_data = frame.get("body")
        if body_data and pb_root:
            body_mat = coordinator.unity_to_blender_matrix(
                body_data.get("position", {}),
                body_data.get("rotation", {})
            )
            pb_root.matrix = body_mat
            pb_root.keyframe_insert(data_path="location", frame=blender_frame)
            pb_root.keyframe_insert(data_path="rotation_euler", frame=blender_frame)

        context.view_layer.update()

        head_data = frame.get("head")
        if head_data and pb_head:
            r_world_head = coordinator.unity_to_blender_rotation(head_data.get("rotation", {})).to_matrix().to_4x4()
            target_head_matrix = r_world_head @ b_head_mat
            current_head_loc = pb_head.matrix.to_translation()
            new_head_matrix = mathutils.Matrix.Translation(current_head_loc) @ target_head_matrix
            pb_head.matrix = new_head_matrix
            pb_head.keyframe_insert(data_path="rotation_euler", frame=blender_frame)

        lh_data = frame.get("leftHand")
        if lh_data and pb_lh:
            lh_mat = coordinator.unity_to_blender_matrix(
                lh_data.get("position", {}),
                lh_data.get("rotation", {})
            )
            pb_lh.matrix = lh_mat
            pb_lh.keyframe_insert(data_path="location", frame=blender_frame)
            pb_lh.keyframe_insert(data_path="rotation_euler", frame=blender_frame)

        rh_data = frame.get("rightHand")
        if rh_data and pb_rh:
            rh_mat = coordinator.unity_to_blender_matrix(
                rh_data.get("position", {}),
                rh_data.get("rotation", {})
            )
            pb_rh.matrix = rh_mat
            pb_rh.keyframe_insert(data_path="location", frame=blender_frame)
            pb_rh.keyframe_insert(data_path="rotation_euler", frame=blender_frame)

        l_idx_val = max(0.0, min(1.0, float(frame.get("leftIndex", 0.0))))
        l_mid_val = max(0.0, min(1.0, float(frame.get("leftMiddle", 0.0))))
        l_thb_val = max(0.0, min(1.0, float(frame.get("leftThumb", 0.0))))

        if pb_l_index:
            pb_l_index.rotation_euler.z = l_idx_val * rad_75
            pb_l_index.keyframe_insert(data_path="rotation_euler", frame=blender_frame)

        if pb_l_middle:
            pb_l_middle.rotation_euler.z = l_mid_val * rad_75
            pb_l_middle.keyframe_insert(data_path="rotation_euler", frame=blender_frame)

        if pb_l_thumb:
            pb_l_thumb.rotation_euler.x = l_thb_val * rad_65
            pb_l_thumb.keyframe_insert(data_path="rotation_euler", frame=blender_frame)

        r_idx_val = max(0.0, min(1.0, float(frame.get("rightIndex", 0.0))))
        r_mid_val = max(0.0, min(1.0, float(frame.get("rightMiddle", 0.0))))
        r_thb_val = max(0.0, min(1.0, float(frame.get("rightThumb", 0.0))))

        if pb_r_index:
            pb_r_index.rotation_euler.z = r_idx_val * -rad_75
            pb_r_index.keyframe_insert(data_path="rotation_euler", frame=blender_frame)

        if pb_r_middle:
            pb_r_middle.rotation_euler.z = r_mid_val * -rad_75
            pb_r_middle.keyframe_insert(data_path="rotation_euler", frame=blender_frame)

        if pb_r_thumb:
            pb_r_thumb.rotation_euler.x = r_thb_val * rad_65
            pb_r_thumb.keyframe_insert(data_path="rotation_euler", frame=blender_frame)

    context.view_layer.update()

    return {
        "fileName": os.path.basename(file_path),
        "filePath": file_path,
        "collectionName": recording_col.name,
        "armatureName": armature_obj.name,
        "frameCount": frame_count,
        "duration": duration,
        "sampleRate": sample_rate,
        "playerName": player_name,
    }
