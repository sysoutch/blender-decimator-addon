bl_info = {
    "name": "Decimator",
    "author": "Rainer Wahnsinn",
    "version": (1, 1),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > Edit",
    "description": "Decimate mesh to target face count. Merge vertices > Decimate > Apply Modifier.",
    "category": "Object",
}

import bpy
from bpy.props import IntProperty, BoolProperty
from bpy.types import Panel, Operator

class OBJECT_OT_decimate_to_target(Operator):
    bl_idname = "object.decimate_to_target"
    bl_label = "Decimate to Target"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        target_face_count = context.scene.decimate_target_face_count
        current_face_count = len(obj.data.polygons)

        if target_face_count >= current_face_count:
            self.report({'INFO'}, "Target face count is higher than current")
            return {'CANCELLED'}

        # For decimate modifier, ratio = 1.0 means keep all faces
        # ratio = 0.0 means keep no faces
        factor = target_face_count / current_face_count
        factor = max(0.0, min(1.0, factor))  # Clamp between 0 and 1

        # Add decimate modifier
        decimate_mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
        decimate_mod.decimate_type = 'COLLAPSE'
        decimate_mod.ratio = factor
        decimate_mod.use_collapse_triangulate = True

        self.report({'INFO'}, f"Decimated to {target_face_count} faces")
        return {'FINISHED'}

class OBJECT_OT_merge_vertices(Operator):
    bl_idname = "object.merge_vertices"
    bl_label = "Merge Vertices"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        # Store current selection mode
        original_mode = obj.mode
        original_select_mode = context.tool_settings.mesh_select_mode[:]
        
        # Switch to edit mode if needed
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        
        # Set to vertex select mode
        context.tool_settings.mesh_select_mode = (True, False, False)
        
        # Merge vertices
        bpy.ops.mesh.remove_doubles(threshold=0.0001)
        
        # Restore original mode
        bpy.ops.object.mode_set(mode=original_mode)
        
        self.report({'INFO'}, "Vertices merged successfully")
        return {'FINISHED'}

class OBJECT_OT_apply_decimate_modifier(Operator):
    bl_idname = "object.apply_decimate_modifier"
    bl_label = "Apply Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}
        
        # Find and apply the decimate modifier
        for mod in obj.modifiers:
            if mod.type == 'DECIMATE' and mod.name == "Decimate":
                bpy.ops.object.modifier_apply(modifier=mod.name)
                self.report({'INFO'}, "Decimate modifier applied")
                return {'FINISHED'}
        
        self.report({'INFO'}, "No Decimate modifier found")
        return {'CANCELLED'}

class VIEW3D_PT_decimator_panel(Panel):
    bl_label = "Decimator"
    bl_idname = "VIEW3D_PT_decimator_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Edit"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "decimate_target_face_count")
        layout.operator("object.decimate_to_target", text="Decimate")
        
        # Check if decimate modifier exists and show warning
        obj = context.active_object
        if obj and obj.type == 'MESH':
            has_decimate_mod = any(mod.type == 'DECIMATE' and mod.name == "Decimate" for mod in obj.modifiers)
            if has_decimate_mod:
                box = layout.box()
                box.label(text="Model looks off?", icon='QUESTION')
                box.operator("object.merge_vertices", text="Merge Vertices", icon='MOD_VERTEX_WEIGHT')

                box = layout.box()
                box.label(text="Modifier not applied yet", icon='ERROR')
                box.operator("object.apply_decimate_modifier", text="Apply Modifier", icon='FILE_TICK')

def register():
    bpy.utils.register_class(OBJECT_OT_decimate_to_target)
    bpy.utils.register_class(OBJECT_OT_merge_vertices)
    bpy.utils.register_class(OBJECT_OT_apply_decimate_modifier)
    bpy.utils.register_class(VIEW3D_PT_decimator_panel)
    bpy.types.Scene.decimate_target_face_count = IntProperty(
        name="Target Face Count",
        default=1000,
        min=1,
        description="Target number of faces after decimation"
    )

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_decimate_to_target)
    bpy.utils.unregister_class(OBJECT_OT_merge_vertices)
    bpy.utils.unregister_class(OBJECT_OT_apply_decimate_modifier)
    bpy.utils.unregister_class(VIEW3D_PT_decimator_panel)
    del bpy.types.Scene.decimate_target_face_count

if __name__ == "__main__":
    register()
