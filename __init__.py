bl_info = {
    "name": "MonkeFrames Mocap",
    "author": "MonkeFrames Team",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > MonkeFrames Tab",
    "description": "Import MonkeFrames .mfmc motion capture files onto embedded Gorilla Tag rigs.",
    "category": "Import-Export",
}

import bpy
from bpy.props import StringProperty, IntProperty, FloatProperty, PointerProperty
from bpy_extras.io_utils import ImportHelper

from . import importer

class MonkeFramesMocapSettings(bpy.types.PropertyGroup):
    recording_name: StringProperty(
        name="Recording",
        default="None"
    )
    file_path: StringProperty(
        name="File Path",
        default=""
    )
    status: StringProperty(
        name="Status",
        default="No recording loaded"
    )
    fps: IntProperty(
        name="FPS",
        default=24
    )
    frame_count: IntProperty(
        name="Frames",
        default=0
    )
    duration_str: StringProperty(
        name="Duration",
        default="00:00.00"
    )
    rig_name: StringProperty(
        name="Rig",
        default="Fuldxx Rig V5.0"
    )
    collection_name: StringProperty(
        name="Collection",
        default=""
    )

class MONKEFRAMES_OT_import_mocap(bpy.types.Operator, ImportHelper):
    bl_idname = "monkeframes.import_mocap"
    bl_label = "Import Mocap (.mfmc)"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".mfmc"
    filter_glob: StringProperty(
        default="*.mfmc",
        options={'HIDDEN'}
    )

    def execute(self, context):
        settings = context.scene.monkeframes_mocap
        try:
            res = importer.import_mocap_file(self.filepath, context)

            settings.file_path = res["filePath"]
            settings.recording_name = res["fileName"]
            settings.collection_name = res["collectionName"]
            settings.fps = round(res["sampleRate"])
            settings.frame_count = res["frameCount"]

            dur = res["duration"]
            mins = int(dur // 60)
            secs = dur % 60
            settings.duration_str = f"{mins:02d}:{secs:05.2f}"
            settings.status = f"Loaded {res['frameCount']} frames ({settings.duration_str})"

            self.report({'INFO'}, f"Successfully imported {res['fileName']}.")
            return {'FINISHED'}

        except Exception as ex:
            settings.status = f"Error: {ex}"
            self.report({'ERROR'}, f"Mocap import failed: {ex}")
            return {'CANCELLED'}

class MONKEFRAMES_OT_reimport_mocap(bpy.types.Operator):
    bl_idname = "monkeframes.reimport_mocap"
    bl_label = "Import / Rebuild"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.monkeframes_mocap
        return bool(settings.file_path)

    def execute(self, context):
        settings = context.scene.monkeframes_mocap
        try:
            res = importer.import_mocap_file(settings.file_path, context)
            settings.collection_name = res["collectionName"]
            settings.fps = round(res["sampleRate"])
            settings.frame_count = res["frameCount"]

            dur = res["duration"]
            mins = int(dur // 60)
            secs = dur % 60
            settings.duration_str = f"{mins:02d}:{secs:05.2f}"
            settings.status = f"Rebuilt {res['frameCount']} frames ({settings.duration_str})"

            self.report({'INFO'}, f"Rebuilt {res['fileName']}.")
            return {'FINISHED'}
        except Exception as ex:
            settings.status = f"Error: {ex}"
            self.report({'ERROR'}, f"Rebuild failed: {ex}")
            return {'CANCELLED'}

class MONKEFRAMES_OT_remove_rig(bpy.types.Operator):
    bl_idname = "monkeframes.remove_rig"
    bl_label = "Remove Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.monkeframes_mocap
        return bool(settings.collection_name) and (settings.collection_name in bpy.data.collections)

    def execute(self, context):
        settings = context.scene.monkeframes_mocap
        col = bpy.data.collections.get(settings.collection_name)
        if col:
            for obj in list(col.all_objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(col)

        settings.collection_name = ""
        settings.recording_name = "None"
        settings.frame_count = 0
        settings.status = "Rig removed"
        self.report({'INFO'}, "Removed mocap rig and collection.")
        return {'FINISHED'}

class MONKEFRAMES_PT_mocap_panel(bpy.types.Panel):
    bl_label = "MOCAP"
    bl_idname = "MONKEFRAMES_PT_mocap_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MonkeFrames'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.monkeframes_mocap

        col = layout.column(align=True)
        col.scale_y = 1.3
        col.operator("monkeframes.import_mocap", text="Import Mocap (.mfmc)", icon='IMPORT')

        layout.separator()

        box = layout.box()
        box.label(text="Recording Details:", icon='INFO')

        row = box.row()
        row.label(text="Recording:")
        row.label(text=settings.recording_name)

        row = box.row()
        row.label(text="Status:")
        row.label(text=settings.status)

        if settings.recording_name != "None" and settings.frame_count > 0:
            box.separator()

            row = box.row()
            row.label(text="FPS:")
            row.label(text=str(settings.fps))

            row = box.row()
            row.label(text="Frames:")
            row.label(text=str(settings.frame_count))

            row = box.row()
            row.label(text="Duration:")
            row.label(text=settings.duration_str)

            row = box.row()
            row.label(text="Rig:")
            row.label(text=settings.rig_name)

            layout.separator()

            col_actions = layout.column(align=True)
            col_actions.operator("monkeframes.reimport_mocap", text="Import / Rebuild", icon='FILE_REFRESH')
            col_actions.operator("monkeframes.remove_rig", text="Remove Rig", icon='TRASH')

classes = (
    MonkeFramesMocapSettings,
    MONKEFRAMES_OT_import_mocap,
    MONKEFRAMES_OT_reimport_mocap,
    MONKEFRAMES_OT_remove_rig,
    MONKEFRAMES_PT_mocap_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.monkeframes_mocap = PointerProperty(type=MonkeFramesMocapSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "monkeframes_mocap"):
        del bpy.types.Scene.monkeframes_mocap

if __name__ == "__main__":
    register()
