# ~~~~~~~~~ BEGIN LICENSE BLOCK ~~~~~~~~~
#
#  Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0) 
#
#  This work is licensed under the Creative Commons
#  Attribution-NonCommercial-NoDerivatives 4.0 International License. 
#
#  To view a copy of this license,
#  visit http://creativecommons.org/licenses/by-nc-nd/4.0/.
#
#  Email : kevthomas2712@gmail.com
#
#  Interested in entering in to partnerships or collaborations, just email
#
# ~~~~~~~~~ END LICENSE BLOCK ~~~~~~~~~

bl_info = {
    "name": "NamePlate Generator",
    "author": "Kev Thomas",
    "version": (1, 4.2),
    "blender": (2, 91, 2),
    "location": "View3D > UI > NamePlate Tab",
    "description": "Adds a new NamePlate Object with user defined properties",
    "warning": "",
    "wiki_url": "",
    "category": "User Interface",
}
import bpy, mathutils
from bpy.types import Panel, Operator
from bpy.props import FloatProperty
from mathutils import Matrix, Vector
import os

pi = 3.14159                    #   Math function 

#~ NURNIE ICON PREVIEW MENU
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
def enum_previews_from_directory_items(self, context):
    """EnumProperty callback"""
    enum_items = []

    if context is None:
        return enum_items

    wm = context.window_manager
    directory = wm.my_previews_dir

    pcoll = preview_collections["main"]

    if directory == pcoll.my_previews_dir:
        return pcoll.my_previews

    print("Scanning directory: %s" % directory)

    if directory and os.path.exists(directory):
        image_paths = []
        for fn in os.listdir(directory):
            if fn.lower().endswith(".png"):
                image_paths.append(fn)

        for i, name in enumerate(image_paths):
            filepath = os.path.join(directory, name)
            icon = pcoll.get(name)
            if not icon:
                thumb = pcoll.load(name, filepath, 'IMAGE')
            else:
                thumb = pcoll[name]
            enum_items.append((name, name, "", thumb.icon_id, i))

    pcoll.my_previews = enum_items
    pcoll.my_previews_dir = directory
    return pcoll.my_previews

#~ ITALICS
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
def italicText(self,context):
    if bpy.context.scene.my_tool.it_bot_text == True:
        bpy.context.object.data.shear = 0.2
    else:
        bpy.context.object.data.shear = 0.0
    
#~ UNHIDE HIDDEN OBJECTS PRIOR TO EDITING
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
def unhidenurnieleft(self):
    bpy.data.objects["NUR_LEFT"].hide_set(False)
def unhidenurnieright(self):
    bpy.data.objects["NUR_RIGHT"].hide_set(False)    

#~ MOVE OBJECTS ON THEIR LOCAL AXIS RATHER THAN WORLD
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
def get_locationZ(self):
    return self.get('locationZ', 0)

def set_locationZ(self, value):
    z_axis = Vector((0, 1, 0))
    delta = value - self.get('locationZ', 0)
    v = (self.matrix_world.to_3x3() @ z_axis).normalized()

    self.matrix_world.translation += delta * v
    self['locationZ'] = value

def get_locationY(self):
    return self.get('locationY', 0)

def set_locationY(self, value):
    y_axis = Vector((0, 0, 1))
    ydelta = value - self.get('locationY', 0)
    yv = (self.matrix_world.to_3x3() @ y_axis).normalized()

    self.matrix_world.translation += ydelta * yv
    self['locationY'] = value
        
#~ POINTER MENU FOR WHAT TO EDIT
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
def selectItem(self, context):
    
    menu= bpy.context.scene.objects.get(str(bpy.context.scene.my_tool.my_item))

    if menu:
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = menu
        menu.select_set(True)
    else:
        default= bpy.context.scene.objects.get("BASE")
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = default
        default.select_set(True)
        
        
#~ DROP DOWN MENU CHANGER FOR BASE TYPES
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
def selectBase(self, context):
    selectedbasetype="my_"+(bpy.context.scene.my_tool.my_baselist)

#~ AUTODRAW OPTION
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
def drawPlate(self, context):
    if bpy.context.scene.my_tool.autodraw == True:
        drawPlateTrue(self, context)
        
    if bpy.context.scene.my_tool.autodraw == False:  
        return    

#~ MAKE DUPLCATES REAL *(NURNIES)*
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
def SetNurnie(self, context):
        
    if 'NURNIE_LEFT' in bpy.context.scene.objects: 
        ob = bpy.context.scene.objects["NURNIE_LEFT"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        unhidenurnieleft(self)
        ob = bpy.context.scene.objects["NUR_LEFT"] 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.duplicate()  
        bpy.ops.object.duplicates_make_real()  
        bpy.data.objects.remove(bpy.data.objects['NURNIE_LEFT.001'], do_unlink=True)
        bpy.data.objects.remove(bpy.data.objects['NUR_LEFT.001'], do_unlink=True)
        bpy.data.objects["NUR_LEFT"].hide_set(True)
        
    if 'NURNIE_RIGHT' in bpy.context.scene.objects: 
        ob = bpy.context.scene.objects["NURNIE_RIGHT"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        unhidenurnieright(self)
        ob = bpy.context.scene.objects["NUR_RIGHT"] 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.duplicate()  
        bpy.ops.object.duplicates_make_real()  
        bpy.data.objects.remove(bpy.data.objects['NURNIE_RIGHT.001'], do_unlink=True)
        bpy.data.objects.remove(bpy.data.objects['NUR_RIGHT.001'], do_unlink=True)
        bpy.data.objects["NUR_RIGHT"].hide_set(True)

#~ DRAW PLATE - REMOVE EXISTING BEFORE DRAW
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
def drawPlateTrue(self, context):
    def halfscale(x, y, z):
        return (x * 0.5, y * 0.5, z * 0.5)

    # Oval / Lobed data
    O035 = ()
    O042 = ()
    O052 = ()
    O070 = ()
    O092 = ()
    O095 = ()
    O105 = ()
    L060 = ((30.3, 34.4), (44.1, 54.7), (51.7, 67))
    L075 = ((36.9, 33), (54, 51), (63.3, 63.3))
    L090 = ((45.5, 34.8), (65.8, 53.7), (77.4, 66.3))
    L105 = ((59.4, 46.3), (83.8, 67.9), (96.8, 81.3))
    L120 = ((76.1, 58.1), (105, 83.5), (120, 98.2))
    L150 = ((81.9, 41.7), (116, 62.6), (135, 76.1))
    L170 = ((87.5, 40.5), (125, 60.3), (145, 73.1))

    # Parameters from UI
    base_obj = bpy.data.objects["BASE"]
    base_type = base_obj.data.name[:1]
    base_size_x = int(base_obj.data.name[1:4])
    base_string_x = base_obj.data.name[1:4]
    base_size_y = int(base_obj.data.name[4:7])
    end_length = int(bpy.context.scene.my_tool.end_length)
    circle_curve = int(bpy.context.scene.my_tool.angles) * 0.01
    if circle_curve == 0.41:
        circle_curve = 0.415
    oval_choice = int(bpy.context.scene.my_tool.o_angles)
    my_main_ends = bpy.context.scene.my_tool.my_main_ends
    user_z = int(bpy.context.scene.my_tool.my_user_z)
    top_height = int(bpy.context.scene.my_tool.my_top_height) * 0.5
    top_panel_curve = int(bpy.context.scene.my_tool.top_angles) * 0.01
    user_y = 1
    border_thickness = 0.5
    border_depth = 0.5

    top_position = user_z + top_height * 0.5 if not bpy.data.window_managers["WinMan"].my_operator_toggle else user_z

    # Length and curvature calculation
    if base_type == "C":
        radius = base_size_x * 0.5
        circumference = 2 * pi * radius
        arc_length = circumference * circle_curve
        user_x = arc_length - (end_length * 2)
        curve_x = arc_length / radius

    elif base_type == "O":
        base_selected = eval(base_type + base_string_x)
        user_x = base_selected[0] - (end_length * 2)
        curve_x = base_selected[1] * pi / 180

    elif base_type == "L":
        base_selected = eval(base_type + base_string_x)
        user_x = base_selected[oval_choice][0] - (end_length * 2)
        curve_x = base_selected[oval_choice][1] * pi / 180

    elif base_type == "S":
        user_x = base_size_y - (end_length * 2)
        curve_x = 0

    elif base_type == "Z":
        base_size_y = base_size_x
        radius = base_size_x * 0.5
        arc_length = (2 * pi * radius) * circle_curve
        user_x = arc_length - (end_length * 2)
        curve_x = arc_length / radius

    # Build base plate
    for name in ['NameplateBase', 'NameplateTop', 'NameplateBottom']:
        if name in bpy.context.scene.objects:
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

    loc_y = -base_size_y * 0.5
    if bpy.context.scene.my_tool.eng_bot:
        bpy.ops.mesh.primitive_cube_add(align='WORLD', location=(0, loc_y - 0.25, user_z * 0.5),
                                        scale=halfscale(user_x, 1.5, user_z))
    else:
        bpy.ops.mesh.primitive_cube_add(align='WORLD', location=(0, loc_y, user_z * 0.5),
                                        scale=halfscale(user_x, user_y, user_z))
    bpy.context.active_object.name = 'NameplateBase'

    bpy.ops.mesh.primitive_cube_add(align='WORLD',
        location=(0, loc_y - (user_y - border_thickness * 0.5), user_z - (border_thickness * 0.5)),
        scale=halfscale(user_x, border_depth, border_thickness))
    bpy.context.active_object.name = 'NameplateTop'

    bpy.ops.mesh.primitive_cube_add(align='WORLD',
        location=(0, loc_y - (user_y - border_thickness * 0.5), border_thickness * 0.5),
        scale=halfscale(user_x, border_depth, border_thickness))
    bpy.context.active_object.name = 'NameplateBottom'

    # Top section
    if bpy.context.scene.my_tool.add_top:
        if 'TopBit' in bpy.context.scene.objects:
            bpy.data.objects.remove(bpy.data.objects['TopBit'], do_unlink=True)

        bpy.ops.mesh.primitive_cube_add(align='WORLD',
            location=(0, loc_y - border_thickness * 0.5, top_position),
            scale=halfscale(user_x * top_panel_curve, user_y + border_thickness, top_height))
        c = bpy.context.active_object
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(True)
        bpy.ops.mesh.select_mode(type="EDGE")
        bpy.ops.object.editmode_toggle()
        c.data.edges[2].select = True
        c.data.edges[8].select = True
        bpy.ops.object.editmode_toggle()
        bevel_type = bpy.context.scene.my_tool.my_top_ends
        if bevel_type == "BEVEL":
            bpy.ops.mesh.bevel(offset=1.85688, segments=10)
        elif bevel_type == "CHAMFER":
            bpy.ops.mesh.bevel(offset=1.0, segments=10, affect='EDGES', profile=0.1)
        elif bevel_type == "SLANT":
            bpy.ops.mesh.bevel(offset=1.1, segments=0)
        bpy.ops.object.editmode_toggle()
        c.name = 'TopBit'
    elif 'TopBit' in bpy.context.scene.objects:
        bpy.data.objects.remove(bpy.data.objects['TopBit'], do_unlink=True)

    # Ends
    for side, sign, edge_1, edge_2, name in [("LEFT", -1, 0, 2, 'END_LEFT'), ("RIGHT", 1, 7, 8, 'END_RIGHT')]:
        if name in bpy.context.scene.objects:
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
        loc = (sign * ((user_x * 0.5) + (end_length * 0.5)),
               -((base_size_y + border_thickness) * 0.5),
               user_z * 0.5)
        bpy.ops.mesh.primitive_cube_add(align='WORLD', location=loc,
                                        scale=halfscale(end_length, (user_y + border_thickness), user_z ))
        c = bpy.context.active_object
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(True)
        bpy.ops.mesh.select_mode(type="EDGE")
        bpy.ops.object.editmode_toggle()
        c.data.edges[edge_1].select = True
        c.data.edges[edge_2].select = True
        bpy.ops.object.editmode_toggle()
        if my_main_ends == "BEVEL":
            bpy.ops.mesh.bevel(offset=1.85688, segments=10)
        elif my_main_ends == "CHAMFER":
            bpy.ops.mesh.bevel(offset=1.0, segments=10, affect='EDGES', profile=0.1)
        elif my_main_ends == "SLANT":
            bpy.ops.mesh.bevel(offset=1.1, segments=0)
        bpy.ops.object.editmode_toggle()
        c.name = name

    # Plate assembly
    bpy.context.scene.cursor.location = [0, -base_size_y * 0.5, 0]
    if 'PLATE' in bpy.context.scene.objects:
        bpy.data.objects.remove(bpy.data.objects['PLATE'], do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in ("NameplateBottom", "NameplateTop", "END_LEFT", "END_RIGHT", "TopBit", "NameplateBase"):
        obj = bpy.context.scene.objects.get(o)

        if obj:
            obj.select_set(True)
    bpy.ops.object.join()
    bpy.context.active_object.name = 'PLATE'

    bpy.context.object.location[2] = -0.15
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        
    bpy.ops.object.modifier_add(type='REMESH')
    bpy.context.object.modifiers["Remesh"].voxel_size = 0.05

    # Tilt the plate
    bpy.ops.transform.rotate(value=0.261799, orient_axis='X', orient_type='GLOBAL')

    #Wrap the plate
    bpy.ops.object.modifier_add(type='SIMPLE_DEFORM')
    bpy.context.object.modifiers["SimpleDeform"].deform_method = 'BEND'
    bpy.context.object.modifiers["SimpleDeform"].deform_axis = 'Z'
    bpy.context.object.modifiers["SimpleDeform"].origin = bpy.data.objects["EMPTY"]
    bpy.context.object.modifiers["SimpleDeform"].angle = curve_x

    bpy.context.object.location[2] = user_z * 0.5 + 0.2
           
         
#~ DRAW 90DEGREE ARC
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def drawFOV(self, context):
    
    if bpy.context.scene.my_tool.fov_option == True:
        if 'FOV' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['FOV'], do_unlink=True)
        
        base_size_x=int(bpy.data.objects["BASE"].data.name[1:4])
        user_z=int(bpy.context.scene.my_tool.my_user_z)   

        bpy.ops.view3d.snap_cursor_to_center()
        bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(-((base_size_x*.5)+2)*.5,.5,user_z+.02), scale=((base_size_x*.5)+2, 1, 1)) 
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.context.object.rotation_euler[2] = 0.785398
        bpy.context.active_object.name = 'FOV1'

        bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(((base_size_x*.5)+2)*.5,.5,user_z+.02), scale=((base_size_x*.5)+2, 1, 1)) 
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.context.object.rotation_euler[2] = -0.785398
        bpy.context.active_object.name = 'FOV2'
        for o in ("FOV1", "FOV2"):
            obj = bpy.context.scene.objects.get(o)
            if obj: obj.select_set(True)
        bpy.ops.object.join()
        bpy.context.active_object.name = 'FOV'
    else:
        if 'FOV' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['FOV'], do_unlink=True)
        
    ob = bpy.context.scene.objects["PLATE"] 
    bpy.ops.object.select_all(action='DESELECT') 
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True) 
    
    
#~ DRAW CIRCLE BASES AND BEZIER PATH 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
def drawCBase(self, context):
    # Remove existing related objects if they exist
    for name in ['PATH', 'BASE', 'EMPTY']:
        obj = bpy.context.scene.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Get base sizes from property string (e.g., 'C025025')
    base_size_x = int(bpy.context.scene.my_tool.my_BCIRCLE[1:4])  # diameter
    base_size_y = int(bpy.context.scene.my_tool.my_BCIRCLE[4:])  # diameter

    # Add a Bezier circle path with true radius
    bpy.ops.curve.primitive_bezier_circle_add(
        radius=base_size_x * 0.5,
        enter_editmode=False,
        align='WORLD',
        location=(0, 0, 0)
    )
    path = bpy.context.active_object
    bpy.context.view_layer.objects.active = path
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.switch_direction()
    bpy.ops.object.mode_set(mode='OBJECT')
    path.name = 'PATH'

    # Add the base mesh as a properly scaled cylinder
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=base_size_x * 0.5,
        depth=4,
        enter_editmode=False,
        align='WORLD',
        location=(0, 0, 2)
    )
    base = bpy.context.active_object
    base.name = 'BASE'
    base.data.name = bpy.context.scene.my_tool.my_BCIRCLE
    bpy.context.view_layer.objects.active = base
    base.select_set(True)

    # Go into Edit mode and select only the top face
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.object.mode_set(mode='OBJECT')

    # Select the top face (last index)
    top_index = max(
    range(len(base.data.polygons)),
    key=lambda i: sum(base.data.vertices[v].co.z for v in base.data.polygons[i].vertices) / len(base.data.polygons[i].vertices)
)
    base.data.polygons[top_index].select = True

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.transform.resize(
        value=(
            (base_size_x - 2) / base_size_x,
            (base_size_y - 2) / base_size_y,
            1
        ),
        orient_type='GLOBAL'
    )
    bpy.ops.object.mode_set(mode='OBJECT')

    # Optional: Set viewport shading to random color
    area = next((a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'), None)
    if area:
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.color_type = 'RANDOM'


#~ DRAW OVAL BASES AND ADD BEZIER CIRCLE AS PATH - REMOVE EXISTING BEFORE DRAW
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
def drawOBase(self, context):
    if 'PATH' in bpy.context.scene.objects: 
        bpy.data.objects.remove(bpy.data.objects['PATH'], do_unlink=True)
    if 'BASE' in bpy.context.scene.objects: 
        bpy.data.objects.remove(bpy.data.objects['BASE'], do_unlink=True)
         
    base_size_x=int(bpy.context.scene.my_tool.my_BOVAL[1:4])
    base_size_y=int(bpy.context.scene.my_tool.my_BOVAL[4:7])
    bpy.ops.curve.primitive_bezier_circle_add(radius=1, enter_editmode=True, align='WORLD', location=(0, 0, 0), scale=( 1, 1, 1))
    bpy.ops.curve.switch_direction()
    bpy.ops.object.editmode_toggle()
    bpy.context.object.scale[0] = base_size_x*.5
    bpy.context.object.scale[1] = base_size_y*.5
    bpy.context.active_object.name = 'PATH' 
    
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, enter_editmode=True, align='WORLD', location=(0, 0, 2), scale=(base_size_x,base_size_y, 4))
    c = bpy.context.active_object
    bpy.ops.mesh.select_all(True)
    bpy.ops.object.editmode_toggle()
    c.data.polygons[62].select = True
    bpy.ops.object.editmode_toggle()
    bpy.ops.transform.resize(value=((base_size_x-2)/base_size_x, (base_size_y-2)/base_size_y, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.object.editmode_toggle()
    bpy.context.active_object.name = 'BASE'  
    bpy.context.active_object.data.name = bpy.context.scene.my_tool.my_BOVAL

    bpy.context.space_data.shading.color_type = 'RANDOM'

#~ DRAW OVAL BASES AND ADD BEZIER CIRCLE AS PATH - REMOVE EXISTING BEFORE DRAW
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
def drawSBase(self, context):
    if 'PATH' in bpy.context.scene.objects: 
        bpy.data.objects.remove(bpy.data.objects['PATH'], do_unlink=True)
    if 'BASE' in bpy.context.scene.objects: 
        bpy.data.objects.remove(bpy.data.objects['BASE'], do_unlink=True)
         
    base_size_x=int(bpy.context.scene.my_tool.my_BSQUARE[1:4])
    base_size_y=int(bpy.context.scene.my_tool.my_BSQUARE[4:7])
    bpy.ops.curve.primitive_nurbs_path_add(radius=base_size_x*.25, enter_editmode=False, align='WORLD', location=(0, -base_size_y*.5, 0), scale=(1, 1, 1))
    bpy.context.active_object.name = 'PATH'
    
    bpy.ops.mesh.primitive_cube_add(enter_editmode=True, align='WORLD', location=(0, 0, 2), scale=(base_size_x,base_size_y, 4))
    c = bpy.context.active_object
    bpy.ops.mesh.select_all(True)
    bpy.ops.object.editmode_toggle()
    c.data.polygons[5].select = True
    bpy.ops.object.editmode_toggle()
    bpy.ops.transform.resize(value=((base_size_x-2)/base_size_x, (base_size_y-2)/base_size_y, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.object.editmode_toggle()
    bpy.context.active_object.name = 'BASE'
    bpy.context.active_object.data.name = bpy.context.scene.my_tool.my_BSQUARE

    bpy.context.space_data.shading.color_type = 'RANDOM'

#~ DRAW OVAL BASES AND ADD BEZIER CIRCLE AS PATH - REMOVE EXISTING BEFORE DRAW
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
def drawZBase(self, context):
    if 'PATH' in bpy.context.scene.objects: 
        bpy.data.objects.remove(bpy.data.objects['PATH'], do_unlink=True)
    if 'BASE' in bpy.context.scene.objects: 
        bpy.data.objects.remove(bpy.data.objects['BASE'], do_unlink=True)
         
    base_size_x=int(bpy.context.scene.my_tool.my_BSPECIAL[1:4])
    base_size_y=int(bpy.context.scene.my_tool.my_BSPECIAL[4:7])
    bpy.ops.curve.primitive_bezier_circle_add(radius=base_size_x*.5, enter_editmode=True, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.ops.curve.switch_direction()
    bpy.ops.object.editmode_toggle()
    bpy.context.active_object.name = 'PATH' 

    bpy.ops.mesh.primitive_cylinder_add(vertices=64, enter_editmode=True, align='WORLD', location=(0, 0, 2), scale=(base_size_x,base_size_x, 4))
    c = bpy.context.active_object
    bpy.ops.mesh.select_all(True)
    bpy.ops.object.editmode_toggle()
    c.data.polygons[62].select = True
    bpy.ops.object.editmode_toggle()
    bpy.ops.transform.resize(value=((base_size_x-2)/(base_size_x), (base_size_x-2)/(base_size_x), 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.mesh.select_all(action = 'DESELECT')
    bpy.ops.object.editmode_toggle()
    for x in range(0, 16):
        c.data.polygons[x].select = True
    for x in range(48, 62):
        c.data.polygons[x].select = True
    for x in range(63, 65):
        c.data.polygons[x].select = True
    bpy.ops.object.editmode_toggle()
    bpy.ops.transform.translate(value=(0, base_size_y-base_size_x, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.object.editmode_toggle()

    bpy.context.active_object.name = 'BASE'
    bpy.context.active_object.data.name = bpy.context.scene.my_tool.my_BSPECIAL
    
    bpy.context.space_data.shading.color_type = 'RANDOM'

#~ PROPERTY GROUP 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
class MyProperties(bpy.types.PropertyGroup):
    
    basic_options : bpy.props.BoolProperty(name="", default=True)
    addit_options : bpy.props.BoolProperty(name="", default=False)
    top_options : bpy.props.BoolProperty(name="", default=False)
    maintext_options : bpy.props.BoolProperty(name="", default=False)
    toptext_options : bpy.props.BoolProperty(name="", default=False)
    
    add_top : bpy.props.BoolProperty(name="", default=False, update = drawPlate)
    top_position : bpy.props.BoolProperty(name="", default=True, update = drawPlate)
    #eng_top : bpy.props.BoolProperty(name="", default=False)
    eng_bot : bpy.props.BoolProperty(name="", default=False, update = drawPlate)
    
    eng_top_text : bpy.props.BoolProperty(name="", default=False)
    it_top_text : bpy.props.BoolProperty(name="", default=False, update = italicText)
    eng_bot_text : bpy.props.BoolProperty(name="", default=False)
    it_bot_text : bpy.props.BoolProperty(name="", default=False, update = italicText)
    
    fov_option : bpy.props.BoolProperty(name="", default=False, update = drawFOV)
    autodraw : bpy.props.BoolProperty(name="", default=True, update = drawPlate)
    bpy.types.WindowManager.my_operator_toggle = bpy.props.BoolProperty(update = drawPlate)
    
    my_baselist : bpy.props.EnumProperty(
        items= [('BCIRCLE', "Circle Bases", ""),
                ('BOVAL', "Oval Bases", ""),
                ('BSQUARE', "Square Bases", ""),
                ('BSPECIAL', "Special Bases", ""),        
        ],
        default="BCIRCLE",
        update = selectBase
    )       
    
    my_BSPECIAL : bpy.props.EnumProperty(
        items= [('Z025070', "70X25 40K BIKE", ""),
                ('Z040095', "95X40 40K BIKE", ""),
            ],
        update = drawZBase
    )
       
    my_BCIRCLE : bpy.props.EnumProperty(
        items= [('C025025', "25mm Circle", ""),
                ('C032032', "32mm Circle", ""),
                ('C040040', "40mm Circle", ""),
                ('C050050', "50mm Circle", ""),
                ('C060060', "60mm Circle", ""),
                ('C080080', "80mm Circle", ""),
                ('C100100', "100mm Circle", ""),
                ('C130130', "130mm Circle", ""),
                ('C160160', "160mm Circle", ""),
            ],
        update = drawCBase
    )
    
    my_BSQUARE : bpy.props.EnumProperty(
        items= [('S025025', "25mm Square", ""),
                ('S032032', "32mm Square", ""),
                ('S040040', "40mm Square", ""),
                ('S050050', "50mm Square", ""),
                ('S060060', "60mm Square", ""),
                ('S080080', "80mm Square", ""),
                ('S100100', "100mm Square", ""),
                ('S130130', "130mm Square", ""),
                ('S160160', "160mm Square", ""),
            ],
        update = drawSBase
    )
    
    my_BOVAL : bpy.props.EnumProperty(
        items= [#('O035060', "60x35mm Oval Short Edge", ""),
                ('L060035', "60x35mm Oval Long Edge", ""),
                #('O042075', "75x42mm Oval Short Edge", ""),
                ('L075042', "75x42mm Oval Long Edge", ""),
                #('O052090', "90x52mm Oval Short Edge", ""),
                ('L090052', "90x52mm Oval Long Edge", ""),
                #('O070105', "105x70mm Oval Short Edge", ""),
                ('L105070', "105x70mm Oval Long Edge", ""),
                #('O092120', "120x92mm Oval Short Edge", ""),
                ('L120092', "120x92mm Oval Long Edge", ""),
                #('O095150', "150x95mm Oval Short Edge", ""),
                ('L150095', "150x95mm Oval Long Edge", ""),
                #('O105170', "170x105mm Oval Short Edge", ""),
                ('L170105', "170x105mm Oval Long Edge", ""),            
        ],
        update = drawOBase
    )
    
    my_user_z : bpy.props.EnumProperty(
        items= [('3', "3mm", ""),
                ('4', "4mm", ""),
                ('5', "5mm", ""),
                ('6', "6mm", ""),
        ],
        default='4',
        update = drawPlate
    )
    
    my_main_ends : bpy.props.EnumProperty(
        items= [('PLAIN', "Plain", ""),
                ('BEVEL', "Round", ""),
                ('SLANT', "Slanted", ""),
                ('CHAMFER', "Chamfered", ""),
        ],
        default='PLAIN',
        update = drawPlate
    )
    
    my_top_ends : bpy.props.EnumProperty(
        items= [('PLAIN', "Plain", ""),
                ('BEVEL', "Round", ""),
                ('SLANT', "Slanted", ""),
                ('CHAMFER', "Chamfered", ""),
        ],
        default='PLAIN',
        update = drawPlate
    )
    
    my_top_height : bpy.props.EnumProperty(
        items= [('3', "1.5mm", ""),
                ('4', "2mm", ""),
                ('5', "2.5mm", ""),
                ('6', "3mm", ""),
        ],
        default='4',
        update = drawPlate
    )
     
    end_length: bpy.props.EnumProperty(
        items= [('2', "2mm End Caps", ""),
                ('3', "3mm End Caps", ""),
                ('4', "4mm End Caps", ""),
                ('5', "5mm End Caps", ""),
                ('6', "6mm End Caps", ""),
        ],
        default='4',
        update = drawPlate
    )
    
    top_angles : bpy.props.EnumProperty(
        items=[
            ("25", "1/4 Base Coverage", ""),
            ("50", "1/2 Base Coverage", ""),
            ("75", "3/4 Coverage", ""),
            ("100", "Full Coverage", ""),        
         ],
        default="50",
        update = drawPlate
    )
    
    o_angles : bpy.props.EnumProperty(
        items=[
            ("0", "90 Degrees", "90 Degrees"),
            ("1", "120 Degrees", "120 Degrees"),
            ("2", "135 Degrees", "135 Degrees"),     
         ],
        default="0",
        update = drawPlate
    )
    
    angles : bpy.props.EnumProperty(
        items=[
            ("25", "90 Degrees", "90 Degrees"),
            ("33", "120 Degrees", "120 Degrees"),
            ("41", "150 Degrees", "150 Degrees"),
            ("50", "180 Degrees", "180 Degrees"),
                
         ],
        default="41",
        update = drawPlate
    ) 
    
    my_item : bpy.props.EnumProperty(
        items=[
            ('PLATE', "Nameplate", ""),
            ('UPPERTEXT', "Upper Text", ""),
            ('MAINTEXT', "Main Text",  ""),
            ('NURNIE_LEFT', "Left Nurnie", ""),
            ('NURNIE_RIGHT', "Right Nurnie", ""),
        ],
        default="PLATE",
        update = selectItem
    ) 

    my_newbase : bpy.props.EnumProperty(
        items= [("NEW", "NEW", "NEW"),
                ("IMPORT", "IMPORT", "IMPORT"),
            ]
    )

#~ IMPORT PLATE AND RENAME    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

class Import_STL_Custom(bpy.types.Operator):
    bl_idname = "object.import_stl_custom"
    bl_label = "Import STL Custom"

    filepath : bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob : bpy.props.StringProperty(
        default="*.stl;",
        options={'HIDDEN'},
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        bpy.ops.wm.stl_import(filepath=self.filepath)
        for obj in bpy.context.selected_objects:
            obj.name = "IMPORTPLATE"
            obj.data.name = "IMPORTPLATE"
        return {"FINISHED"}

#~ MESSAGE BOX 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

def ShowMessageBox(message = "", title = "", icon = ''):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
    
#~ EXPORT PLATE  
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

class Export_STL_Custom(bpy.types.Operator):
    bl_idname = "object.export_stl_custom"
    bl_label = "Export STL Custom"

    filepath : bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob : bpy.props.StringProperty(
        default="*.stl;",
        options={'HIDDEN'},
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        SetNurnie(self, context)
        
        ob = bpy.context.scene.objects["PLATE"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True) 
        if ob.modifiers:
            bpy.ops.object.modifier_add(type='DECIMATE')
            bpy.context.object.modifiers["Decimate"].ratio = 0.01
            bpy.ops.object.modifier_apply(modifier="Remesh")
            bpy.ops.object.modifier_apply(modifier="SimpleDeform")
            bpy.ops.object.modifier_apply(modifier="Decimate")
        
        if 'FOV' in bpy.context.scene.objects: 
            ob = bpy.context.scene.objects["PLATE"] 
            bpy.ops.object.select_all(action='DESELECT') 
            bpy.context.view_layer.objects.active = ob
            ob.select_set(True) 
            bpy.ops.object.modifier_add(type='BOOLEAN')
            bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
            bpy.context.object.modifiers["Boolean"].solver = 'FAST'
            bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["FOV"]
            bpy.ops.object.modifier_apply(modifier="Boolean")
            bpy.data.objects.remove(bpy.data.objects['FOV'], do_unlink=True)
            
        if bpy.context.scene.my_tool.eng_bot_text == True and 'MAINTEXT' in bpy.context.scene.objects: 
            select_main = ""
            ob = bpy.context.scene.objects["MAINTEXT"] 
            bpy.ops.object.select_all(action='DESELECT') 
            bpy.context.view_layer.objects.active = ob
            ob.select_set(True) 
            bpy.ops.object.duplicate(linked=False)
            bpy.ops.object.convert(target='MESH')
            bpy.context.active_object.name = 'MAINTEXTBOOL'  

            ob = bpy.context.scene.objects["PLATE"] 
            bpy.ops.object.select_all(action='DESELECT') 
            bpy.context.view_layer.objects.active = ob
            ob.select_set(True) 
            bpy.ops.object.modifier_add(type='BOOLEAN')
            bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
            bpy.context.object.modifiers["Boolean"].solver = 'FAST'
            bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["MAINTEXTBOOL"]
            bpy.ops.object.modifier_apply(modifier="Boolean")
            bpy.data.objects.remove(bpy.data.objects['MAINTEXTBOOL'], do_unlink=True)
        else:
            select_main = "MAINTEXT"    
            
        if bpy.context.scene.my_tool.eng_top_text == True and 'UPPERTEXT' in bpy.context.scene.objects:
            select_upper = ""
            ob = bpy.context.scene.objects["UPPERTEXT"] 
            bpy.ops.object.select_all(action='DESELECT') 
            bpy.context.view_layer.objects.active = ob
            ob.select_set(True) 
            bpy.ops.object.duplicate(linked=False)
            bpy.ops.object.convert(target='MESH')
            bpy.context.active_object.name = 'UPPERTEXTBOOL'  

            ob = bpy.context.scene.objects["PLATE"] 
            bpy.ops.object.select_all(action='DESELECT') 
            bpy.context.view_layer.objects.active = ob
            ob.select_set(True) 
            bpy.ops.object.modifier_add(type='BOOLEAN')
            bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
            bpy.context.object.modifiers["Boolean"].solver = 'FAST'
            bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["UPPERTEXTBOOL"]
            bpy.ops.object.modifier_apply(modifier="Boolean")
            bpy.data.objects.remove(bpy.data.objects['UPPERTEXTBOOL'], do_unlink=True)
        else:
            select_upper = "UPPERTEXT"
            
        bpy.ops.object.select_all(action='DESELECT')
        for o in bpy.data.objects:
            if o.name in (select_upper, select_main, "PLATE", "NUR_RIGHT.002", "NUR_LEFT.002"):
                o.select_set(True)
        if self.filepath.endswith('.stl'): bpy.ops.export_mesh.stl(filepath=self.filepath,use_selection=True,check_existing=True,use_mesh_modifiers=True)
        else: bpy.ops.wm.stl_export(filepath=self.filepath+".stl",export_selected_objects=True,apply_modifiers=True,check_existing=True)
        
        filename, extension = os.path.splitext(self.filepath)
        
        if 'NUR_LEFT.002' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NUR_LEFT.002'], do_unlink=True)
        if 'NUR_RIGHT.002' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NUR_RIGHT.002'], do_unlink=True)
        
        ob = bpy.context.scene.objects["PLATE"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True) 
        
        ShowMessageBox("Nameplate Saved", "Saved STL", 'DISK_DRIVE')

        return {"FINISHED"}
#~ MAIN UI  
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
class OBJECT_PT_NamePlate(Panel):
    bl_label = ""
    bl_idname = "OBJECT_PT_nameplate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Name Plate"
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="Name Plate Maker v1.14", icon= 'WORDWRAP_ON')
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager
        obj = context.object
                
        if 'BASE' in bpy.context.scene.objects: 
            base_type=bpy.data.objects["BASE"].data.name[:1]
        
        if 'PLATE' in bpy.context.scene.objects:
            box = layout.box()
            box.label(text= "Choose what to edit", icon= 'GREASEPENCIL')
            box.prop(mytool, "my_item", expand=True) 
            box.label(text= "Options:", icon= 'LIGHT_DATA')
            box.operator("object.export_stl_custom", text="Save Your STL", icon='DISK_DRIVE') 
            box.operator("clear_scene.myop_operator", text="Start Over", icon='RECOVER_LAST') 
            if 'IMPORTPLATE' not in bpy.context.scene.objects:  
                box.operator("draw.myop_operator", text="Clear Any Engraves", icon='BRUSH_DATA')  
            if obj.name=='NURNIE_LEFT':
                box = layout.box()
                box.label(text= "Edit Nurnie position:", icon= 'SMALL_CAPS')
                if base_type=="S": loc_text="<< Left / Right >>" 
                else: loc_text="<< Around Circle >>"
                box.prop(obj, 'location', index=0, text=loc_text) 
                box.prop(obj, 'myNurnZFloat', slider=False)
                box.prop(obj, 'myNurnYFloat', slider=False)
                box.prop(obj, "instance_faces_scale", text="<< Scale >>", slider=False) 
                box.operator("flipnurnieleft.myop_operator", text="Flip Nurnie", icon='MOD_MIRROR') 
                box.operator("mirrornurnieleft.myop_operator", text="Mirror Nurnie On Plate", icon='UV_SYNC_SELECT')
                   
                box = layout.box()
                box.label(text= "Change Your Nurnie")
                box.prop(wm, "my_previews_dir")
                box.template_icon_view(wm, "my_previews")
                box.operator("changenurnieleft.myop_operator", text="Change Nurnie", icon='FILE_REFRESH')
                box = layout.box()
                box.operator("deletenurnieleft.myop_operator", text="Remove Nurnie", icon='TRASH')
            elif mytool.my_item == 'NURNIE_LEFT' and 'NURNIE_LEFT' not in bpy.context.scene.objects and obj.name=="BASE":
                box = layout.box()
                box.label(text= "Add your Left Hand Nurnie")
                box.prop(wm, "my_previews_dir")
                box.template_icon_view(wm, "my_previews")
                box.operator("addnurnieleft.myop_operator")
                    
            if obj.name=='NURNIE_RIGHT':     
                box = layout.box()
                box.label(text= "Edit Nurnie position:", icon= 'SMALL_CAPS')
                if base_type=="S": loc_text="<< Left / Right >>" 
                else: loc_text="<< Around Circle >>"
                box.prop(obj, 'location', index=0, text=loc_text) 
                box.prop(obj, 'myNurnZFloat', slider=False)
                box.prop(obj, 'myNurnYFloat', slider=False)
                box.prop(obj, "instance_faces_scale", text="<< Scale >>", slider=False) 
                box.operator("flipnurnieright.myop_operator", text="Flip Nurnie", icon='MOD_MIRROR') 
                box.operator("mirrornurnieright.myop_operator", text="Mirror Nurnie On Plate", icon='UV_SYNC_SELECT')
                box = layout.box()
                box.label(text= "Change Your Nurnie")
                box.prop(wm, "my_previews_dir")
                box.template_icon_view(wm, "my_previews")
                box.operator("changenurnieright.myop_operator", text="Change Nurnie", icon='FILE_REFRESH')
                box = layout.box()
                box.operator("deletenurnieright.myop_operator", text="Remove Nurnie", icon='TRASH')
            elif mytool.my_item == 'NURNIE_RIGHT' and 'NURNIE_RIGHT' not in bpy.context.scene.objects and obj.name=="BASE":
                box = layout.box()
                box.label(text= "Add your Right Hand Nurnie")
                box.prop(wm, "my_previews_dir")
                box.template_icon_view(wm, "my_previews")
                box.operator("addnurnieright.myop_operator")

            if obj.name == 'UPPERTEXT':
                box = layout.box()
                text = context.object.data    
                      
                box.label(text= "Edit your text:", icon= 'SMALL_CAPS')
                box.prop(text, 'body', text = "")    
                        
                box = layout.box()
                box.label(text= "Choose Font:", icon= 'SMALL_CAPS')
                box.template_ID(text, "font", open="font.open", unlink="font.unlink")          
                row = box.row()
                if mytool.eng_bot_text == False:
                    row.label(text= "Engrave Text On Export?")
                    row.prop(mytool, "eng_top_text")
                else:
                    row.label(text= "Engrave Text On!", icon= 'SCULPTMODE_HLT')
                    row.prop(mytool, "eng_top_text")
                row = box.row()
                if mytool.it_bot_text == False:
                    row.label(text="Italic Text Off")
                    row.prop(mytool, "it_bot_text")   
                if mytool.it_bot_text == True:
                    row.label(text="Italic Text On", icon= 'ITALIC')
                    row.prop(mytool, "it_bot_text")
                box.prop(text, "size", text="Text Size") 
                box.label(text= "Adjust Text Position:", icon= 'ORIENTATION_GLOBAL')
                box.prop(obj, 'myZFloat', slider=False)
                box.prop(obj, 'myYFloat', slider=False)
                
                box = layout.box()
                row = box.row()
                row.prop(mytool, "maintext_options")
                row.label(text="Text Extra Options")
                if mytool.maintext_options == True:  
                    box.label(text= "Set the Spacing Options:", icon= 'CENTER_ONLY')
                    row = box.row()
                    row.label(text= "Character:")
                    row.prop(text, "space_character", text= "")
                    row = box.row()
                    row.label(text= "Words:")
                    row.prop(text, "space_word", text= "")
                    box.operator("increasevoxel.myop_operator", text="Increase Text Clarity", icon='MOD_THICKNESS')
                    box.operator("decreasevoxel.myop_operator", text="Decrease Text Clarity", icon='MOD_SMOOTH')       
            elif mytool.my_item == 'UPPERTEXT' and 'UPPERTEXT' not in bpy.context.scene.objects:
                box = layout.box()
                box.label(text= "Add your UPPER text")
                #box.operator("wm.textopbasic", text= "Click to open window", icon= 'OUTLINER_OB_FONT')

            if obj.name == 'MAINTEXT':
                box = layout.box()
                text = context.object.data    
                      
                box.label(text= "Edit your text:", icon= 'SMALL_CAPS')
                box.prop(text, 'body', text = "")    
                        
                box = layout.box()
                box.label(text= "Choose Font:", icon= 'SMALL_CAPS')
                box.template_ID(text, "font", open="font.open", unlink="font.unlink")          
                row = box.row()
                if mytool.eng_bot_text == False:
                    row.label(text= "Engrave Text On Export?")
                    row.prop(mytool, "eng_bot_text")
                else:
                    row.label(text= "Engrave Text On!", icon= 'SCULPTMODE_HLT')
                    row.prop(mytool, "eng_bot_text")
                row = box.row()
                if mytool.it_bot_text == False:
                    row.label(text="Italic Text Off")
                    row.prop(mytool, "it_bot_text")   
                if mytool.it_bot_text == True:
                    row.label(text="Italic Text On", icon= 'ITALIC')
                    row.prop(mytool, "it_bot_text")
                box.prop(text, "size", text="Text Size") 
                box.label(text= "Adjust Text Position:", icon= 'ORIENTATION_GLOBAL')
                box.prop(obj, 'myZFloat', slider=False)
                box.prop(obj, 'myYFloat', slider=False)
                
                box = layout.box()
                row = box.row()
                row.prop(mytool, "maintext_options")
                row.label(text="Text Extra Options")
                if mytool.maintext_options == True:  
                    box.label(text= "Set the Spacing Options:", icon= 'CENTER_ONLY')
                    row = box.row()
                    row.label(text= "Character:")
                    row.prop(text, "space_character", text= "")
                    row = box.row()
                    row.label(text= "Words:")
                    row.prop(text, "space_word", text= "")
                    box.operator("increasevoxel.myop_operator", text="Increase Text Clarity", icon='MOD_THICKNESS')
                    box.operator("decreasevoxel.myop_operator", text="Decrease Text Clarity", icon='MOD_SMOOTH')
            elif mytool.my_item == 'MAINTEXT' and 'MAINTEXT' not in bpy.context.scene.objects:
                box = layout.box()
                box.label(text= "Add your MAIN text")
                #box.operator("wm.textopbasic", text= "Click to open window", icon= 'OUTLINER_OB_FONT')          

            if obj.name == 'PLATE':                             
                if 'IMPORTPLATE' in bpy.context.scene.objects:      
                    box = layout.box()
                    box.label(text= "Edit your nameplate position", icon= 'ORIENTATION_GLOBAL')
                    box.prop(obj, 'location', index=2, text='Adjust Up/Down:')
                    box.prop(obj, 'location', index=1, text='Adjust Back/Forward:')  
                else:                     
                    row = box.row()
                    if mytool.autodraw == False:
                        row.label(text="Turn Autodraw On/Off")
                        row.prop(mytool, "autodraw")
                        box.operator("draw.myop_operator", text="Create Plate", icon='GREASEPENCIL')    
                    if mytool.autodraw == True:
                        row.label(text="Turn Autodraw Off/On")
                        row.prop(mytool, "autodraw")

                    box = layout.box()
                    row = box.row()
                    row.prop(mytool, "basic_options")
                    row.label(text="Basic Plate Options")
                    if mytool.basic_options == True:
                        row = box.row()
                        row.label(text="Engravable/Plain Plate")
                        row.prop(mytool, "eng_bot") 
                        if mytool.my_baselist == "BCIRCLE":
                            box.label(text= "Arc of nameplate", icon= 'PROP_PROJECTED')
                            box.prop(mytool, "angles", expand=True)
                        if mytool.my_baselist == "BSPECIAL":
                            box.label(text= "Arc of nameplate", icon= 'PROP_PROJECTED')
                            box.prop(mytool, "angles", expand=True)
                        if mytool.my_baselist == "BOVAL":
                            if base_type == "L":
                                box.label(text= "Arc of nameplate", icon= 'PROP_PROJECTED')
                                box.prop(mytool, "o_angles", expand=True)
                            if base_type == "O":
                                box.label(text= "Only comes in 90degrees")
                                
                        box.label(text= "Choose your basic design", icon= 'IMAGE_ALPHA')
                        box.prop(mytool, "my_main_ends", expand=True)
                        box.label(text= "Choose your end cap width", icon= 'FACE_MAPS')
                        box.prop(mytool, "end_length", expand=True)
                        box.label(text= "Choose your height", icon= 'EMPTY_SINGLE_ARROW')
                        box.prop(mytool, "my_user_z", expand=True)       
                   
                    box = layout.box()
                    row = box.row()
                    row.prop(mytool, "top_options")
                    row.label(text="Top Plate Options")
                    if mytool.top_options == True:
                        row = box.row()
                        row.label(text="Add top plate")
                        row.prop(mytool, "add_top")
                        box.label(text="Choose top plate height!", icon='EXPORT')
                        box.prop(mytool, "my_top_height", expand=True)
                        box.label(text= "Length of plate", icon= 'PROP_PROJECTED')
                        box.prop(mytool, "top_angles", expand=True)
                        box.label(text="Choose position of top plate!")
                        label = "Put On Top" if wm.my_operator_toggle else "Drop Half Way"
                        icon = 'ANCHOR_TOP' if wm.my_operator_toggle else 'ANCHOR_CENTER'
                        box.prop(wm, 'my_operator_toggle', text=label, icon=icon, toggle=True)
                        box.label(text="Choose top plate design!")  
                        box.prop(mytool, "my_top_ends", expand=True)
                        
                    box = layout.box()
                    row = box.row()
                    row.prop(mytool, "addit_options")
                    row.label(text="Advanced options")
                    if mytool.addit_options == True:
                        row = box.row()
                        row.label(text="Add FOV cut out", icon='LINCURVE')
                        row.prop(mytool, "fov_option")
                        #row.label(text="End cap height", icon='EMPTY_SINGLE_ARROW')
                        #row.prop(mytool, "end_height")
                        #row.label(text="End cap depth", icon='FACESEL')
                        #row.prop(mytool, "end_depth")
                        
                
        elif 'IMPORTPLATE' in bpy.context.scene.objects:            
            if 'EMPTY' not in bpy.context.scene.objects:
                box = layout.box()
                box.operator("wm.importhelp", text="!!PLEASE READ!!")           
                box.label(text= "Choose your base shape", icon= 'PROP_ON')
                box.prop(mytool, "my_baselist", expand=True)
                box.label(text= "Choose your base size", icon= 'PROP_ON')
                box.prop(mytool, "my_"+(bpy.context.scene.my_tool.my_baselist), expand=True) 
                if 'BASE' in bpy.context.scene.objects:
                    box.operator("getready.myop_operator", text="Confirm Base Choice", icon='CHECKBOX_HLT')
         
        elif 'EMPTY' not in bpy.context.scene.objects:
            
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
                
                if 'EMPTY' not in bpy.context.scene.objects:
                    box = layout.box()
                    box.label(text="Create a Brand New plate!", icon='FILE_NEW')
                    
                    box = layout.box()
                    box.label(text= "Choose your base shape", icon= 'PROP_ON')
                    box.prop(mytool, "my_baselist", expand=True)
                    box.label(text= "Choose your base size", icon= 'PROP_ON')
                    box.prop(mytool, "my_"+(bpy.context.scene.my_tool.my_baselist), expand=True) 
                    if 'BASE' in bpy.context.scene.objects:
                        box.operator("getready.myop_operator", text="Confirm Base Choice", icon='FILE_NEW')
                                                             
preview_collections = {}

#~ HELP WINDOW
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~             
class WM_OT_ImportHelpWindow(Operator):
    bl_idname = "wm.importhelp"
    bl_label = "Note regarding imported bases"
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
       
    def draw(self, context):
        scene = context.scene
        mytool = scene.my_tool
        layout = self.layout

        layout.label(text= "------------------------------------------------------------------------------------------")
        layout.label(text= "Some imported baseplates (Mostly those designed")
        layout.label(text= "by other creators) may not automatically align to the")
        layout.label(text= "world centre. Please align the imported plate to the")
        layout.label(text= "chosen base shape and size in the next step")
        layout.label(text= "-----------------")
        layout.label(text= "This is an slightly advanced step, and will require ")
        layout.label(text= "you to know the basics of blender to move and rotate")
        layout.label(text= "the nameplate and viewport to suit your needs")
        
    def execute(self, context):

        return {'FINISHED'}

#~ INCREASE VOXEL COUNT
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
class INCREASETEXTVOXEL_OT_my_op(Operator):
    bl_label = "Increase Text Voxel"
    bl_idname = "increasevoxel.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        
        cur_size = bpy.context.object.modifiers["Remesh"].voxel_size
        new_size = cur_size-0.01
        if cur_size > 0.019:
            bpy.context.object.modifiers["Remesh"].voxel_size = new_size
        
        return {'FINISHED'}

#~ DECREASE VOXEL COUNT
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
class DECREASETEXTVOXEL_OT_my_op(Operator):
    bl_label = "Decrease Text Voxel"
    bl_idname = "decreasevoxel.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        
        cur_size = bpy.context.object.modifiers["Remesh"].voxel_size
        new_size = cur_size+0.01
        bpy.context.object.modifiers["Remesh"].voxel_size = new_size
        
        return {'FINISHED'}
    
#~ OPERATOR FOR DRAWPLATE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      
class DRAW_OT_my_op(Operator):
    bl_label = "Draw"
    bl_idname = "draw.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager  
        
        drawPlateTrue(self, context)
        
        return {'FINISHED'}  
        
#~ OPERATOR FOR CLEARING SCENE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      
class CLEARSCENE_OT_my_op(Operator):
    bl_label = "Clear Scene"
    bl_idname = "clear_scene.myop_operator"
    bl_description = "Clear The Scene"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager  
        if 'NURNIE_LEFT' in bpy.context.scene.objects: 
            unhidenurnieleft(self)
        if 'NURNIE_RIGHT' in bpy.context.scene.objects: 
            unhidenurnieright(self)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        return {'FINISHED'}  

#~ MAKE DUPLCATES REAL RIGHT NURNIE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
class SETNURNIERIGHT_OT_my_op(Operator):
    bl_label = "Set Nurnie"
    bl_idname = "setnurnieright.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        
        bpy.ops.object.duplicates_make_real()  
        
        ob = bpy.context.scene.objects["NUR_RIGHT.001"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.context.active_object.name = 'RIGHT_NURNIE'  
        
        if 'NURNIE_RIGHT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NURNIE_RIGHT'], do_unlink=True)
        if 'NUR_RIGHT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NUR_RIGHT'], do_unlink=True)
        
        return {'FINISHED'}

#~ MIRROR LEFT NURNIE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~              
class MIRRORNURNIELEFT_OT_my_op(Operator):
    bl_label = "Mirror Nurnie Left"
    bl_idname = "mirrornurnieleft.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager
        
        base_type=bpy.data.objects["BASE"].data.name[:1]
        base_size_x=int(bpy.data.objects["BASE"].data.name[1:4])
        base_size_y=int(bpy.data.objects["BASE"].data.name[4:7])
        
        if 'NURNIE_RIGHT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NURNIE_RIGHT'], do_unlink=True)
        if 'NUR_RIGHT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NUR_RIGHT'], do_unlink=True)
        
        nurnie_x = -bpy.data.objects['NURNIE_LEFT'].location.x
        nurnie_y = bpy.data.objects['NURNIE_LEFT'].location.y
        nurnie_z = bpy.data.objects['NURNIE_LEFT'].location.z
        nurnie_s = bpy.data.objects['NURNIE_LEFT'].instance_faces_scale
        
        unhidenurnieleft(self)
        
        ob = bpy.context.scene.objects["NUR_LEFT"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.duplicate()  
        bpy.ops.object.parent_clear(type='CLEAR')
        bpy.context.active_object.name = 'NUR_RIGHT'
        
        circle_curve=int(bpy.context.scene.my_tool.angles)*.01
        if circle_curve==.41: circle_curve=.415
        
        if base_type=="S":
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=((base_size_x-2, -base_size_y*.5-.5, 2)))            
        else:
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(((base_size_x*pi)*.25)+((base_size_x*pi)*circle_curve*.5)-(float(bpy.context.scene.my_tool.end_length)*.5), -1.5, int(bpy.context.scene.my_tool.my_user_z)*.5))
            #bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(((base_size_x*pi)/2)-2, -1, 2))
        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        bpy.context.active_object.name = 'NURNIE_RIGHT'  
        bpy.context.object.location[0] = nurnie_x
        bpy.context.object.location[1] = nurnie_y
        bpy.context.object.location[2] = nurnie_z
        
        bpy.data.objects['NUR_RIGHT'].parent = bpy.data.objects['NURNIE_RIGHT']   
        bpy.ops.object.modifier_add(type='CURVE')
        bpy.context.object.modifiers["Curve"].object = bpy.data.objects["PATH"]
        bpy.context.object.instance_type = 'FACES' 
        
        bpy.context.object.show_instancer_for_render = False
        bpy.context.object.show_instancer_for_viewport = False

        bpy.context.object.use_instance_faces_scale = True
        bpy.context.object.instance_faces_scale = nurnie_s
        bpy.context.object.rotation_euler[0] = -0.261799
        
        bpy.data.objects["NUR_LEFT"].hide_set(True)
        bpy.data.objects["NUR_RIGHT"].hide_set(True)
        
        ob = bpy.context.scene.objects["NURNIE_LEFT"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)       
        return {'FINISHED'}

#~ MIRROR RIGHT NURNIE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~              
class MIRRORNURNIERIGHT_OT_my_op(Operator):
    bl_label = "Mirror Nurnie Right"
    bl_idname = "mirrornurnieright.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager
        
        base_type=bpy.data.objects["BASE"].data.name[:1]
        base_size_x=int(bpy.data.objects["BASE"].data.name[1:4])
        base_size_y=int(bpy.data.objects["BASE"].data.name[4:7])
        
        if 'NURNIE_LEFT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NURNIE_LEFT'], do_unlink=True)
        if 'NUR_LEFT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NUR_LEFT'], do_unlink=True)
        
        ob = bpy.context.scene.objects["NURNIE_RIGHT"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        
        nurnie_x = bpy.data.objects['NURNIE_RIGHT'].location.x
        nurnie_y = bpy.data.objects['NURNIE_RIGHT'].location.y
        nurnie_z = bpy.data.objects['NURNIE_RIGHT'].location.z
        nurnie_s = bpy.data.objects['NURNIE_RIGHT'].instance_faces_scale
        
        unhidenurnieright(self)
        
        ob = bpy.context.scene.objects["NUR_RIGHT"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.duplicate()  
        bpy.ops.object.parent_clear(type='CLEAR')
        bpy.context.active_object.name = 'NUR_LEFT'
        
        circle_curve=int(bpy.context.scene.my_tool.angles)*.01
        if circle_curve==.41: circle_curve=.415
        
        if base_type=="S":
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(2, -base_size_y*.5-.5, 2))            
        else:
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(((base_size_x*pi)*.25)-((base_size_x*pi)*circle_curve*.5)+(float(bpy.context.scene.my_tool.end_length)*.5), -1.5, int(bpy.context.scene.my_tool.my_user_z)*.5))
            #bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(2, -1, 2))
        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        bpy.context.active_object.name = 'NURNIE_LEFT'  
        bpy.context.object.location[0] = -nurnie_x
        bpy.context.object.location[1] = nurnie_y
        bpy.context.object.location[2] = nurnie_z
        
        bpy.data.objects['NUR_LEFT'].parent = bpy.data.objects['NURNIE_LEFT']   
        bpy.ops.object.modifier_add(type='CURVE')
        bpy.context.object.modifiers["Curve"].object = bpy.data.objects["PATH"]
        bpy.context.object.instance_type = 'FACES'  
        
        bpy.context.object.show_instancer_for_render = False
        bpy.context.object.show_instancer_for_viewport = False

        bpy.context.object.use_instance_faces_scale = True
        bpy.context.object.instance_faces_scale = nurnie_s
        bpy.context.object.rotation_euler[0] = -0.261799
        
        bpy.data.objects["NUR_LEFT"].hide_set(True)
        bpy.data.objects["NUR_RIGHT"].hide_set(True)
        
        ob = bpy.context.scene.objects["NURNIE_RIGHT"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)      
        
        return {'FINISHED'}

#~ DELETE LEFT NURNIE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~              
class DELETENURNIELEFT_OT_my_op(Operator):
    bl_label = "Delete Nurnie"
    bl_idname = "deletenurnieleft.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager
        
        if 'NURNIE_LEFT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NURNIE_LEFT'], do_unlink=True)
        if 'NUR_LEFT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NUR_LEFT'], do_unlink=True)
            
        return {'FINISHED'}
            
#~ DELETE RIGHT NURNIE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~              
class DELETENURNIERIGHT_OT_my_op(Operator):
    bl_label = "Delete Nurnie"
    bl_idname = "deletenurnieright.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager
        
        if 'NURNIE_RIGHT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NURNIE_RIGHT'], do_unlink=True)
        if 'NUR_RIGHT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NUR_RIGHT'], do_unlink=True)
        
        return {'FINISHED'}
    
#~ CHANGE LEFT NURNIE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~              
class CHANGENURNIELEFT_OT_my_op(Operator):
    bl_label = "Change Nurnie"
    bl_idname = "changenurnieleft.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager
        
        base_type=bpy.data.objects["BASE"].data.name[:1]
        base_size_x=int(bpy.data.objects["BASE"].data.name[1:4])
        base_size_y=int(bpy.data.objects["BASE"].data.name[4:7])
        
        nurnie_x = bpy.data.objects['NURNIE_LEFT'].location.x
        nurnie_y = bpy.data.objects['NURNIE_LEFT'].location.y
        nurnie_z = bpy.data.objects['NURNIE_LEFT'].location.z
        nurnie_s = bpy.data.objects['NURNIE_LEFT'].instance_faces_scale

        import_dir = wm.my_previews_dir
        import_file = bpy.data.window_managers["WinMan"].my_previews[:-4]

        bpy.ops.wm.stl_import(filepath=import_dir+import_file+".stl") 
               
        if 'NURNIE_LEFT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NURNIE_LEFT'], do_unlink=True)
        if 'NUR_LEFT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NUR_LEFT'], do_unlink=True)
        bpy.context.active_object.name = 'NUR_LEFT'
        
        circle_curve=int(bpy.context.scene.my_tool.angles)*.01
        if circle_curve==.41: circle_curve=.415
            
        if base_type=="S":
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(2, -base_size_y*.5-.5, 2))            
        else:
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(((base_size_x*pi)*.25)-((base_size_x*pi)*circle_curve*.5)+(float(bpy.context.scene.my_tool.end_length)*.5), -1.5, int(bpy.context.scene.my_tool.my_user_z)*.5))
            #bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(2, -1, 2))
        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        bpy.context.active_object.name = 'NURNIE_LEFT'  
        bpy.context.object.location[0] = nurnie_x
        bpy.context.object.location[1] = nurnie_y
        bpy.context.object.location[2] = nurnie_z
              
        bpy.data.objects['NUR_LEFT'].parent = bpy.data.objects['NURNIE_LEFT']   
        bpy.ops.object.modifier_add(type='CURVE')
        bpy.context.object.modifiers["Curve"].object = bpy.data.objects["PATH"]
        bpy.context.object.instance_type = 'FACES'
        
        bpy.context.object.show_instancer_for_render = False
        bpy.context.object.show_instancer_for_viewport = False

        bpy.context.object.use_instance_faces_scale = True
        bpy.context.object.instance_faces_scale = nurnie_s
        bpy.context.object.rotation_euler[0] = -0.261799
        
        bpy.data.objects["NUR_LEFT"].hide_set(True)
        
        return {'FINISHED'}

#~ CHANGE RIGHT NURNIE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~              
class CHANGENURNIERIGHT_OT_my_op(Operator):
    bl_label = "Change Nurnie"
    bl_idname = "changenurnieright.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager
        
        base_type=bpy.data.objects["BASE"].data.name[:1]
        base_size_x=int(bpy.data.objects["BASE"].data.name[1:4])
        base_size_y=int(bpy.data.objects["BASE"].data.name[4:7])
        
        nurnie_x = bpy.data.objects['NURNIE_RIGHT'].location.x
        nurnie_y = bpy.data.objects['NURNIE_RIGHT'].location.y
        nurnie_z = bpy.data.objects['NURNIE_RIGHT'].location.z
        nurnie_s = bpy.data.objects['NURNIE_RIGHT'].instance_faces_scale
            
        import_dir = wm.my_previews_dir
        import_file = bpy.data.window_managers["WinMan"].my_previews[:-4]

        bpy.ops.wm.stl_import(filepath=import_dir+import_file+".stl") 
               
        if 'NURNIE_RIGHT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NURNIE_RIGHT'], do_unlink=True)
        if 'NUR_RIGHT' in bpy.context.scene.objects: 
            bpy.data.objects.remove(bpy.data.objects['NUR_RIGHT'], do_unlink=True)
        bpy.context.active_object.name = 'NUR_RIGHT'
        
        circle_curve=int(bpy.context.scene.my_tool.angles)*.01
        if circle_curve==.41: circle_curve=.415
            
        if base_type=="S":
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=((base_size_x-2, -base_size_y*.5-.5, 2)))            
        else:
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(((base_size_x*pi)*.25)+((base_size_x*pi)*circle_curve*.5)-(float(bpy.context.scene.my_tool.end_length)*.5), -1.5, int(bpy.context.scene.my_tool.my_user_z)*.5))
            #bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(((base_size_x*pi)/2)-2, -1, 2))
        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        bpy.context.active_object.name = 'NURNIE_RIGHT'  
        bpy.context.object.location[0] = nurnie_x
        bpy.context.object.location[1] = nurnie_y
        bpy.context.object.location[2] = nurnie_z
              
        bpy.data.objects['NUR_RIGHT'].parent = bpy.data.objects['NURNIE_RIGHT']   
        bpy.ops.object.modifier_add(type='CURVE')
        bpy.context.object.modifiers["Curve"].object = bpy.data.objects["PATH"]
        bpy.context.object.instance_type = 'FACES'
        
        bpy.context.object.show_instancer_for_render = False
        bpy.context.object.show_instancer_for_viewport = False

        bpy.context.object.use_instance_faces_scale = True
        bpy.context.object.instance_faces_scale = nurnie_s
        bpy.context.object.rotation_euler[0] = -0.261799
        
        bpy.data.objects["NUR_RIGHT"].hide_set(True)
        return {'FINISHED'}
                
#~ IMPORT LEFT NURNIE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~              
class ADDNURNIELEFT_OT_my_op(Operator):
    bl_label = "Import Nurnie Left"
    bl_idname = "addnurnieleft.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager
                
        base_type=bpy.data.objects["BASE"].data.name[:1]
        base_size_x=int(bpy.data.objects["BASE"].data.name[1:4])
        base_size_y=int(bpy.data.objects["BASE"].data.name[4:7])
        
        import_dir = wm.my_previews_dir
        import_file = bpy.data.window_managers["WinMan"].my_previews[:-4]

        bpy.ops.wm.stl_import(filepath=import_dir+import_file+".stl")        
        bpy.context.active_object.name = 'NUR_LEFT' 
        
        circle_curve=int(bpy.context.scene.my_tool.angles)*.01
        if circle_curve==.41: circle_curve=.415
        
        if base_type=="S":
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(2, -base_size_y*.5-.5, 2))            
        else:
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(((base_size_x*pi)*.25)-((base_size_x*pi)*circle_curve*.5)+(float(bpy.context.scene.my_tool.end_length)*.5), -1.5, int(bpy.context.scene.my_tool.my_user_z)*.5))
            #bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(2, -1, 2))
        
        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        bpy.context.active_object.name = 'NURNIE_LEFT'  

        bpy.data.objects['NUR_LEFT'].parent = bpy.data.objects['NURNIE_LEFT']   
        bpy.ops.object.modifier_add(type='CURVE')
        bpy.context.object.modifiers["Curve"].object = bpy.data.objects["PATH"]
        bpy.context.object.instance_type = 'FACES'
        
        bpy.context.object.show_instancer_for_render = False
        bpy.context.object.show_instancer_for_viewport = False

        bpy.context.object.use_instance_faces_scale = True
        bpy.context.object.instance_faces_scale = float(bpy.context.scene.my_tool.my_user_z)
        bpy.context.object.rotation_euler[0] = -0.261799
        
        bpy.data.objects["NUR_LEFT"].hide_set(True)
        return {'FINISHED'}

#~ IMPORT RIGHT NURNIE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~              
class ADDNURNIERIGHT_OT_my_op(Operator):
    bl_label = "Import Nurnie"
    bl_idname = "addnurnieright.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager
                
        base_type=bpy.data.objects["BASE"].data.name[:1]
        base_size_x=int(bpy.data.objects["BASE"].data.name[1:4])
        base_size_y=int(bpy.data.objects["BASE"].data.name[4:7])
        
        import_dir = wm.my_previews_dir
        import_file = bpy.data.window_managers["WinMan"].my_previews[:-4]

        bpy.ops.wm.stl_import(filepath=import_dir+import_file+".stl")        
        bpy.context.active_object.name = 'NUR_RIGHT' 
        
        circle_curve=int(bpy.context.scene.my_tool.angles)*.01
        if circle_curve==.41: circle_curve=.415
    
        if base_type=="S":
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=((base_size_x-2, -base_size_y*.5-.5, 2)))            
        else:
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(((base_size_x*pi)*.25)+((base_size_x*pi)*circle_curve*.5)-(float(bpy.context.scene.my_tool.end_length)*.5), -1.5, int(bpy.context.scene.my_tool.my_user_z)*.5))
        
        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        bpy.context.active_object.name = 'NURNIE_RIGHT'  

        bpy.data.objects['NUR_RIGHT'].parent = bpy.data.objects['NURNIE_RIGHT']   
        bpy.ops.object.modifier_add(type='CURVE')
        bpy.context.object.modifiers["Curve"].object = bpy.data.objects["PATH"]
        bpy.context.object.instance_type = 'FACES'
        
        bpy.context.object.show_instancer_for_render = False
        bpy.context.object.show_instancer_for_viewport = False

        bpy.context.object.use_instance_faces_scale = True
        bpy.context.object.instance_faces_scale = float(bpy.context.scene.my_tool.my_user_z)
        bpy.context.object.rotation_euler[0] = -0.261799
        
        bpy.data.objects["NUR_RIGHT"].hide_set(True)
        return {'FINISHED'}

#~ FLIP LEFT NURNIE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
class FLIPNURNIELEFT_OT_my_op(Operator):
    bl_label = "Flip Nurnie Left"
    bl_idname = "flipnurnieleft.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        
        unhidenurnieleft(self)
          
        ob = bpy.context.scene.objects["NUR_LEFT"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        
   #     bpy.context.object.rotation_euler[0] = 0.523599
        bpy.context.object.rotation_euler[2] = 3.14159
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        
        ob = bpy.context.scene.objects["NURNIE_LEFT"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.data.objects["NUR_LEFT"].hide_set(True)
        
        return {'FINISHED'}
    
#~ FLIP RIGHT NURNIE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
class FLIPNURNIERIGHT_OT_my_op(Operator):
    bl_label = "Flip Nurnie"
    bl_idname = "flipnurnieright.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        
        unhidenurnieright(self)
          
        ob = bpy.context.scene.objects["NUR_RIGHT"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        
     #   bpy.context.object.rotation_euler[0] = 0.523599
        bpy.context.object.rotation_euler[2] = 3.14159
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        
        ob = bpy.context.scene.objects["NURNIE_RIGHT"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.data.objects["NUR_RIGHT"].hide_set(True)
        return {'FINISHED'}

#~ DRAW THE AXIS AND THE TEXT
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        
class Getready_OT_my_op(Operator):
    bl_label = "Get it Ready"
    bl_idname = "getready.myop_operator"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager
        
        if 'Cube' in bpy.context.scene.objects: 
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['Cube'].select_set(True)
            bpy.ops.object.delete()
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['Camera'].select_set(True)
            bpy.ops.object.delete()
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['Light'].select_set(True)
            bpy.ops.object.delete()
                  
        base_type=bpy.data.objects["BASE"].data.name[:1]
        base_size_x=int(bpy.data.objects["BASE"].data.name[1:4])
        base_size_y=int(bpy.data.objects["BASE"].data.name[4:7])
        
        if base_type=="Z":    
            bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, -base_size_x*.5, 0), scale=(1, 1, 1))
        else:
           bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, -base_size_y*.5, 0), scale=(1, 1, 1))
        
        bpy.context.active_object.name = 'EMPTY' 
                
        if 'IMPORTPLATE' not in bpy.context.scene.objects:
            drawPlateTrue(self, context)
        else:
            bpy.data.objects['IMPORTPLATE'].name = 'PLATE'
            bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            bpy.context.active_object.name = 'IMPORTPLATE'   
        
        bpy.ops.object.text_add(enter_editmode=True, align='WORLD', location=[0,-1.1,0], rotation=[1.309,0,0])
        bpy.context.object.data.size = 3
        bpy.context.object.data.extrude = 0.6
        bpy.context.object.data.align_x = 'CENTER'
        bpy.context.object.data.align_y = 'CENTER'
        bpy.context.active_object.name = 'MAINTEXT'
        bpy.ops.font.select_all()
        bpy.ops.font.case_set(case='UPPER')
        bpy.ops.object.editmode_toggle()
        bpy.context.object.data.body = ""
        if base_type=="S":
            bpy.context.object.location[1]= -(base_size_x*.5)-1
            bpy.context.object.data.offset_y = 2.1
        else:
            bpy.context.object.data.offset_x = (base_size_x*pi)*.25
            bpy.ops.object.modifier_add(type='CURVE')
            bpy.context.object.modifiers["Curve"].object = bpy.data.objects["PATH"]
            bpy.context.object.data.offset_y = 2.1
            
        bpy.ops.object.modifier_add(type='REMESH')
        bpy.context.object.modifiers["Remesh"].voxel_size = 0.04
        bpy.context.object.modifiers["Remesh"].use_remove_disconnected = False
        bpy.context.object.modifiers["Remesh"].use_smooth_shade = True

        bpy.ops.object.text_add(enter_editmode=True, align='WORLD', location=[0,-1.5,0], rotation=[1.309,0,0])
        bpy.context.object.data.size = 2
        bpy.context.object.data.extrude = 0.6
        bpy.context.object.data.align_x = 'CENTER'
        bpy.context.object.data.align_y = 'CENTER'
        bpy.context.active_object.name = 'UPPERTEXT'
        bpy.ops.font.select_all()
        bpy.ops.font.case_set(case='UPPER')
        bpy.ops.object.editmode_toggle()
        bpy.context.object.data.body = "" 
        if base_type=="S":
            bpy.context.object.location[1]= -(base_size_x*.5)-1.5
            bpy.context.object.data.offset_y = 5.5
        else:
            bpy.ops.object.modifier_add(type='CURVE')
            bpy.context.object.modifiers["Curve"].object = bpy.data.objects["PATH"]
            bpy.context.object.data.offset_x = (base_size_x*pi)*.25  
            bpy.context.object.data.offset_y = 5.5
            
        bpy.ops.object.modifier_add(type='REMESH')
        bpy.context.object.modifiers["Remesh"].voxel_size = 0.04
        bpy.context.object.modifiers["Remesh"].use_remove_disconnected = False
        bpy.context.object.modifiers["Remesh"].use_smooth_shade = True      
        
        bpy.ops.view3d.view_all(center=False)
        
        ob = bpy.context.scene.objects["PLATE"] 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        
        return {'FINISHED'}

#~ ADDITIONAL PROPERTIES
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~          
bpy.types.Object.myZFloat = FloatProperty(name = "<< Down / Up >>",description = "Set the location on local Z axis",min = -100,max = 100,soft_min=-10,soft_max=10,step=1,subtype='DISTANCE',get = get_locationZ,set = set_locationZ)
bpy.types.Object.myYFloat = FloatProperty(name = "<< Back / Forwards >>",description = "Set the location on local Y axis",min = -100,max = 100,soft_min=-10,soft_max=10,step=1,subtype='DISTANCE',get = get_locationY,set = set_locationY)
bpy.types.Object.myNurnZFloat = FloatProperty(name = "<< Back / Forwards >>",description = "Set the location on local Z axis",min = -100,max = 100,soft_min=-10,soft_max=10,step=1,subtype='DISTANCE',get = get_locationZ,set = set_locationZ)
bpy.types.Object.myNurnYFloat = FloatProperty(name = "<< Down / Up >>",description = "Set the location on local Y axis",min = -100,max = 100,soft_min=-10,soft_max=10,step=1,subtype='DISTANCE',get = get_locationY,set = set_locationY)

#~ 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      
classes = [
    MyProperties, 
    WM_OT_ImportHelpWindow,  
    FLIPNURNIELEFT_OT_my_op,
    ADDNURNIELEFT_OT_my_op, 
    MIRRORNURNIELEFT_OT_my_op,
    SETNURNIERIGHT_OT_my_op, 
    FLIPNURNIERIGHT_OT_my_op,
    ADDNURNIERIGHT_OT_my_op, 
    MIRRORNURNIERIGHT_OT_my_op,
    CHANGENURNIERIGHT_OT_my_op,
    CHANGENURNIELEFT_OT_my_op,
    DELETENURNIELEFT_OT_my_op,
    DELETENURNIERIGHT_OT_my_op,
    CLEARSCENE_OT_my_op,
    DRAW_OT_my_op, 
    Getready_OT_my_op, 
    INCREASETEXTVOXEL_OT_my_op,
    DECREASETEXTVOXEL_OT_my_op,
    OBJECT_PT_NamePlate, 
    Import_STL_Custom,
    Export_STL_Custom
    ]

def register():
 
    from bpy.types import WindowManager
    from bpy.props import (
        StringProperty,
        EnumProperty,
    )
    WindowManager.my_previews_dir = StringProperty(
        name="",
        subtype='DIR_PATH',
        default=""
    )
    WindowManager.my_previews = EnumProperty(
        items=enum_previews_from_directory_items,
    )
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    pcoll.my_previews_dir = ""
    pcoll.my_previews = ()

    preview_collections["main"] = pcoll
    
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type= MyProperties)
 
def unregister():
    
    from bpy.types import WindowManager

    del WindowManager.my_previews

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    
    for cls in classes:
        bpy.utils.unregister_class(cls)

        del bpy.types.Scene.my_tool

if __name__ == "__main__":
    register()