import math
import mathutils

M_ROT = mathutils.Matrix((
    (1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0),
    (0.0, 1.0, 0.0)
))

T_ROT = mathutils.Matrix((
    (-1.0,  0.0, 0.0),
    ( 0.0,  0.0, 1.0),
    ( 0.0, -1.0, 0.0)
))

def unity_to_blender_position(pos_dict_or_vec) -> mathutils.Vector:
    if isinstance(pos_dict_or_vec, dict):
        ux = float(pos_dict_or_vec.get("x", 0.0))
        uy = float(pos_dict_or_vec.get("y", 0.0))
        uz = float(pos_dict_or_vec.get("z", 0.0))
    else:
        ux, uy, uz = pos_dict_or_vec[0], pos_dict_or_vec[1], pos_dict_or_vec[2]

    return mathutils.Vector((ux, uz, uy))

def unity_to_blender_rotation(rot_dict_or_quat) -> mathutils.Quaternion:
    if isinstance(rot_dict_or_quat, dict):
        ux = float(rot_dict_or_quat.get("x", 0.0))
        uy = float(rot_dict_or_quat.get("y", 0.0))
        uz = float(rot_dict_or_quat.get("z", 0.0))
        uw = float(rot_dict_or_quat.get("w", 1.0))
    else:
        uw, ux, uy, uz = rot_dict_or_quat[0], rot_dict_or_quat[1], rot_dict_or_quat[2], rot_dict_or_quat[3]

    q_u = mathutils.Quaternion((uw, ux, uy, uz))
    r_u = q_u.to_matrix()

    r_b = M_ROT @ r_u @ T_ROT
    q_b = r_b.to_quaternion()
    q_b.normalize()
    return q_b

def unity_to_blender_matrix(pos_dict, rot_dict) -> mathutils.Matrix:
    pos_b = unity_to_blender_position(pos_dict)
    rot_b = unity_to_blender_rotation(rot_dict)

    mat = rot_b.to_matrix().to_4x4()
    mat.translation = pos_b
    return mat
