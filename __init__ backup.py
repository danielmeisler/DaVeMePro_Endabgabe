import math
import typing
import bpy

bl_info = {
    "name": "Basic Addon",
    "author": "Samuel Kasper, Alexander Reiprich, David Niemann, Daniel Meisler",
    "version": (1, 0),
    "blender": (2, 91, 0),
    "category": "Add Mesh",
}

def main():
    bpy.ops.object.select_all(action='SELECT') # selektiert alle Objekte
    bpy.ops.object.delete(use_global=False, confirm=False) # löscht selektierte objekte
    bpy.ops.outliner.orphans_purge() # löscht überbleibende Meshdaten etc.
    Method()

class Method():
    def __init__(self):
       print("Init")

class AutostartThing(bpy.types.Operator):
    bl_idname = "object.test"
    bl_label = "test"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main()
        return {'FINISHED'}


def register():
    bpy.utils.register_class(AutostartThing)


def unregister():
    bpy.utils.unregister_class(AutostartThing)


if __name__ == "__main__":
    register()
