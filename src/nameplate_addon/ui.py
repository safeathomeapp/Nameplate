import bpy
from bpy.types import Panel


class OBJECT_PT_NamePlate(Panel):
    bl_label = ""
    bl_idname = "OBJECT_PT_nameplate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Name Plate"

    def draw_header(self, context):
        self.layout.label(text="Name Plate Maker v1.15.2", icon='WORDWRAP_ON')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager
        obj = context.object

        try:
            base_obj = bpy.context.scene.objects.get("BASE")
            plate_obj = bpy.context.scene.objects.get("PLATE")
            empty_obj = bpy.context.scene.objects.get("EMPTY")
            import_plate = bpy.context.scene.objects.get("IMPORTPLATE")
            base_type = base_obj.data.name[:1] if base_obj else ""

            if plate_obj:
                box = layout.box()
                box.label(text="Choose what to edit", icon='GREASEPENCIL')
                box.prop(mytool, "my_item", expand=True)
                box.label(text="Options:", icon='LIGHT_DATA')
                box.operator("object.export_stl_custom", text="Save Your STL", icon='DISK_DRIVE')
                box.operator("clear_scene.myop_operator", text="Start Over", icon='RECOVER_LAST')
                if not import_plate:
                    box.operator("draw.myop_operator", text="Clear Any Engraves", icon='BRUSH_DATA')

                if obj and obj.name == 'NURNIE_LEFT':
                    box = layout.box()
                    box.label(text="Edit Nurnie position:", icon='SMALL_CAPS')
                    loc_text = "<< Left / Right >>" if base_type == "S" else "<< Around Circle >>"
                    box.prop(obj, 'location', index=0, text=loc_text)
                    box.prop(obj, 'myNurnZFloat', slider=False)
                    box.prop(obj, 'myNurnYFloat', slider=False)
                    box.prop(obj, "instance_faces_scale", text="<< Scale >>", slider=False)
                    box.operator("flipnurnieleft.myop_operator", text="Flip Nurnie", icon='MOD_MIRROR')
                    box.operator("mirrornurnieleft.myop_operator", text="Mirror Nurnie On Plate", icon='UV_SYNC_SELECT')

                    box = layout.box()
                    box.label(text="Change Your Nurnie")
                    box.prop(wm, "my_previews_dir")
                    box.template_icon_view(wm, "my_previews")
                    box.operator("changenurnieleft.myop_operator", text="Change Nurnie", icon='FILE_REFRESH')

                    box = layout.box()
                    box.operator("deletenurnieleft.myop_operator", text="Remove Nurnie", icon='TRASH')

                elif mytool.my_item == 'NURNIE_LEFT' and 'NURNIE_LEFT' not in bpy.context.scene.objects and 'BASE' in bpy.context.scene.objects:
                    box = layout.box()
                    box.label(text="Add your Left Hand Nurnie")
                    box.prop(wm, "my_previews_dir")
                    box.template_icon_view(wm, "my_previews")
                    box.operator("addnurnieleft.myop_operator")

                if obj and obj.name == 'NURNIE_RIGHT':
                    box = layout.box()
                    box.label(text="Edit Nurnie position:", icon='SMALL_CAPS')
                    loc_text = "<< Left / Right >>" if base_type == "S" else "<< Around Circle >>"
                    box.prop(obj, 'location', index=0, text=loc_text)
                    box.prop(obj, 'myNurnZFloat', slider=False)
                    box.prop(obj, 'myNurnYFloat', slider=False)
                    box.prop(obj, "instance_faces_scale", text="<< Scale >>", slider=False)
                    box.operator("flipnurnieright.myop_operator", text="Flip Nurnie", icon='MOD_MIRROR')
                    box.operator("mirrornurnieright.myop_operator", text="Mirror Nurnie On Plate", icon='UV_SYNC_SELECT')

                    box = layout.box()
                    box.label(text="Change Your Nurnie")
                    box.prop(wm, "my_previews_dir")
                    box.template_icon_view(wm, "my_previews")
                    box.operator("changenurnieright.myop_operator", text="Change Nurnie", icon='FILE_REFRESH')

                    box = layout.box()
                    box.operator("deletenurnieright.myop_operator", text="Remove Nurnie", icon='TRASH')

                elif mytool.my_item == 'NURNIE_RIGHT' and 'NURNIE_RIGHT' not in bpy.context.scene.objects and 'BASE' in bpy.context.scene.objects:
                    box = layout.box()
                    box.label(text="Add your Right Hand Nurnie")
                    box.prop(wm, "my_previews_dir")
                    box.template_icon_view(wm, "my_previews")
                    box.operator("addnurnieright.myop_operator")

                if obj and obj.name == 'UPPERTEXT':
                    box = layout.box()
                    text = context.object.data
                    box.label(text="Edit your text:", icon='SMALL_CAPS')
                    box.prop(text, 'body', text="")

                    box = layout.box()
                    box.label(text="Choose Font:", icon='SMALL_CAPS')
                    box.template_ID(text, "font", open="font.open", unlink="font.unlink")

                    row = box.row()
                    row.label(text="Engrave Text On Export?")
                    row.prop(mytool, "eng_top_text")

                    row = box.row()
                    row.label(text="Italic")
                    row.prop(mytool, "it_bot_text")

                    box.prop(text, "size", text="Text Size")
                    box.label(text="Adjust Text Position:", icon='ORIENTATION_GLOBAL')
                    box.prop(obj, 'myZFloat', slider=False)
                    box.prop(obj, 'myYFloat', slider=False)

                    box = layout.box()
                    row = box.row()
                    row.prop(mytool, "maintext_options")
                    row.label(text="Text Extra Options")
                    if mytool.maintext_options:
                        box.label(text="Set the Spacing Options:", icon='CENTER_ONLY')
                        row = box.row()
                        row.label(text="Character:")
                        row.prop(text, "space_character", text="")
                        row = box.row()
                        row.label(text="Words:")
                        row.prop(text, "space_word", text="")
                        box.operator("increasevoxel.myop_operator", text="Increase Text Clarity", icon='MOD_THICKNESS')
                        box.operator("decreasevoxel.myop_operator", text="Decrease Text Clarity", icon='MOD_SMOOTH')

                if obj and obj.name == 'MAINTEXT':
                    box = layout.box()
                    text = context.object.data
                    box.label(text="Edit your text:", icon='SMALL_CAPS')
                    box.prop(text, 'body', text="")

                    box = layout.box()
                    box.label(text="Choose Font:", icon='SMALL_CAPS')
                    box.template_ID(text, "font", open="font.open", unlink="font.unlink")

                    row = box.row()
                    row.label(text="Engrave Text On Export?")
                    row.prop(mytool, "eng_bot_text")

                    row = box.row()
                    row.label(text="Italic")
                    row.prop(mytool, "it_bot_text")

                    box.prop(text, "size", text="Text Size")
                    box.label(text="Adjust Text Position:", icon='ORIENTATION_GLOBAL')
                    box.prop(obj, 'myZFloat', slider=False)
                    box.prop(obj, 'myYFloat', slider=False)

                    box = layout.box()
                    row = box.row()
                    row.prop(mytool, "maintext_options")
                    row.label(text="Text Extra Options")
                    if mytool.maintext_options:
                        box.label(text="Set the Spacing Options:", icon='CENTER_ONLY')
                        row = box.row()
                        row.label(text="Character:")
                        row.prop(text, "space_character", text="")
                        row = box.row()
                        row.label(text="Words:")
                        row.prop(text, "space_word", text="")
                        box.operator("increasevoxel.myop_operator", text="Increase Text Clarity", icon='MOD_THICKNESS')
                        box.operator("decreasevoxel.myop_operator", text="Decrease Text Clarity", icon='MOD_SMOOTH')

                if obj and obj.name == 'PLATE':
                    if import_plate:
                        box = layout.box()
                        box.label(text="Edit your nameplate position", icon='ORIENTATION_GLOBAL')
                        box.prop(obj, 'location', index=2, text='Adjust Up/Down:')
                        box.prop(obj, 'location', index=1, text='Adjust Back/Forward:')
                    else:
                        row = layout.row()
                        row.label(text="Autodraw")
                        row.prop(mytool, "autodraw")
                        if not mytool.autodraw:
                            layout.operator("draw.myop_operator", text="Create Plate", icon='GREASEPENCIL')

                        box = layout.box()
                        row = box.row()
                        row.prop(mytool, "basic_options")
                        row.label(text="Basic Plate Options")
                        if mytool.basic_options:
                            row = box.row()
                            row.label(text="Engravable/Plain Plate")
                            row.prop(mytool, "eng_bot")

                            if mytool.my_baselist in {"BCIRCLE", "BSPECIAL"}:
                                box.label(text="Arc of nameplate", icon='PROP_PROJECTED')
                                box.prop(mytool, "angles", expand=True)

                            if mytool.my_baselist == "BOVAL":
                                if base_type == "L":
                                    box.label(text="Arc of nameplate", icon='PROP_PROJECTED')
                                    box.prop(mytool, "o_angles", expand=True)
                                else:
                                    box.label(text="Only comes in 90 degrees")

                            box.label(text="Choose your basic design", icon='IMAGE_ALPHA')
                            box.prop(mytool, "my_main_ends", expand=True)
                            box.label(text="Choose your end cap width", icon='FACE_MAPS')
                            box.prop(mytool, "end_length", expand=True)
                            box.label(text="Choose your height", icon='EMPTY_SINGLE_ARROW')
                            box.prop(mytool, "my_user_z", expand=True)

                        box = layout.box()
                        row = box.row()
                        row.prop(mytool, "top_options")
                        row.label(text="Top Plate Options")
                        if mytool.top_options:
                            row = box.row()
                            row.label(text="Add top plate")
                            row.prop(mytool, "add_top")
                            box.label(text="Choose top plate height!", icon='EXPORT')
                            box.prop(mytool, "my_top_height", expand=True)
                            box.label(text="Length of plate", icon='PROP_PROJECTED')
                            box.prop(mytool, "top_angles", expand=True)
                            label = "Put On Top" if mytool.drop_top_halfway else "Drop Half Way"
                            icon = 'ANCHOR_TOP' if mytool.drop_top_halfway else 'ANCHOR_CENTER'
                            box.prop(mytool, "drop_top_halfway", text=label, icon=icon, toggle=True)
                            box.label(text="Choose top plate design!")
                            box.prop(mytool, "my_top_ends", expand=True)

                        box = layout.box()
                        row = box.row()
                        row.prop(mytool, "addit_options")
                        row.label(text="Advanced options")
                        if mytool.addit_options:
                            row = box.row()
                            row.label(text="Add FOV cut out", icon='LINCURVE')
                            row.prop(mytool, "fov_option")

                return

            if import_plate:
                if not empty_obj:
                    box = layout.box()
                    box.operator("wm.importhelp", text="!!PLEASE READ!!")
                    box.label(text="Choose your base shape", icon='PROP_ON')
                    box.prop(mytool, "my_baselist", expand=True)
                    box.label(text="Choose your base size", icon='PROP_ON')
                    box.prop(mytool, "my_" + mytool.my_baselist, expand=True)
                    if base_obj:
                        box.operator("getready.myop_operator", text="Confirm Base Choice", icon='CHECKBOX_HLT')
                return

            if not empty_obj:
                box = layout.box()
                box.label(text="! LETS GET STARTED !")
                box = layout.box()
                box.label(text="Please select an option")
                layout.prop(mytool, "my_newbase", expand=True)

                if mytool.my_newbase == "IMPORT":
                    box = layout.box()
                    box.label(text="Import a previously saved plate")
                    box = layout.box()
                    box.operator("object.import_stl_custom", text="Import a Saved Plate", icon='FILE_NEW')

                if mytool.my_newbase == "NEW":
                    box = layout.box()
                    box.label(text="Create a Brand New plate!", icon='FILE_NEW')
                    box = layout.box()
                    box.label(text="Choose your base shape", icon='PROP_ON')
                    box.prop(mytool, "my_baselist", expand=True)
                    box.label(text="Choose your base size", icon='PROP_ON')
                    box.prop(mytool, "my_" + mytool.my_baselist, expand=True)
                    if base_obj:
                        box.operator("getready.myop_operator", text="Confirm Base Choice", icon='FILE_NEW')
                return

        except Exception as e:
            layout.label(text="UI error. Check the System Console.", icon='ERROR')
            layout.label(text=str(e)[:80])


def register():
    bpy.utils.register_class(OBJECT_PT_NamePlate)


def unregister():
    bpy.utils.unregister_class(OBJECT_PT_NamePlate)
