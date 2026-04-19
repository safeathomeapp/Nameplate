import bpy
from bpy.props import FloatProperty
from bpy.types import PropertyGroup

from .base import drawCBase, drawOBase, drawSBase, drawZBase
from .helpers import (
    get_locationY,
    get_locationZ,
    italicText,
    selectItem,
    set_locationY,
    set_locationZ,
)
from .operators import drawFOV, selectBase
from .plate import drawPlate


class MyProperties(PropertyGroup):
    basic_options: bpy.props.BoolProperty(name="", default=True)
    addit_options: bpy.props.BoolProperty(name="", default=False)
    top_options: bpy.props.BoolProperty(name="", default=False)
    maintext_options: bpy.props.BoolProperty(name="", default=False)
    toptext_options: bpy.props.BoolProperty(name="", default=False)

    add_top: bpy.props.BoolProperty(name="", default=False, update=drawPlate)
    eng_bot: bpy.props.BoolProperty(name="", default=False, update=drawPlate)

    eng_top_text: bpy.props.BoolProperty(name="", default=False)
    it_top_text: bpy.props.BoolProperty(name="", default=False, update=italicText)
    eng_bot_text: bpy.props.BoolProperty(name="", default=False)
    it_bot_text: bpy.props.BoolProperty(name="", default=False, update=italicText)

    fov_option: bpy.props.BoolProperty(name="", default=False, update=drawFOV)
    autodraw: bpy.props.BoolProperty(name="", default=True, update=drawPlate)

    my_baselist: bpy.props.EnumProperty(
        items=[
            ('BCIRCLE', "Circle Bases", ""),
            ('BOVAL', "Oval Bases", ""),
            ('BSQUARE', "Square Bases", ""),
            ('BSPECIAL', "Special Bases", ""),
        ],
        default="BCIRCLE",
        update=selectBase
    )

    my_BSPECIAL: bpy.props.EnumProperty(
        items=[
            ('Z025070', "70X25 40K BIKE", ""),
            ('Z040095', "95X40 40K BIKE", ""),
        ],
        update=drawZBase
    )

    my_BCIRCLE: bpy.props.EnumProperty(
        items=[
            ('C025025', "25mm Circle", ""),
            ('C032032', "32mm Circle", ""),
            ('C040040', "40mm Circle", ""),
            ('C050050', "50mm Circle", ""),
            ('C060060', "60mm Circle", ""),
            ('C080080', "80mm Circle", ""),
            ('C100100', "100mm Circle", ""),
            ('C130130', "130mm Circle", ""),
            ('C160160', "160mm Circle", ""),
        ],
        update=drawCBase
    )

    my_BSQUARE: bpy.props.EnumProperty(
        items=[
            ('S025025', "25mm Square", ""),
            ('S032032', "32mm Square", ""),
            ('S040040', "40mm Square", ""),
            ('S050050', "50mm Square", ""),
            ('S060060', "60mm Square", ""),
            ('S080080', "80mm Square", ""),
            ('S100100', "100mm Square", ""),
            ('S130130', "130mm Square", ""),
            ('S160160', "160mm Square", ""),
        ],
        update=drawSBase
    )

    my_BOVAL: bpy.props.EnumProperty(
        items=[
            ('L060035', "60x35mm Oval Long Edge", ""),
            ('L075042', "75x42mm Oval Long Edge", ""),
            ('L090052', "90x52mm Oval Long Edge", ""),
            ('L105070', "105x70mm Oval Long Edge", ""),
            ('L120092', "120x92mm Oval Long Edge", ""),
            ('L150095', "150x95mm Oval Long Edge", ""),
            ('L170105', "170x105mm Oval Long Edge", ""),
        ],
        update=drawOBase
    )

    my_user_z: bpy.props.EnumProperty(
        items=[('3', "3mm", ""), ('4', "4mm", ""), ('5', "5mm", ""), ('6', "6mm", "")],
        default='4',
        update=drawPlate
    )

    my_main_ends: bpy.props.EnumProperty(
        items=[('PLAIN', "Plain", ""), ('BEVEL', "Round", ""), ('SLANT', "Slanted", ""), ('CHAMFER', "Chamfered", "")],
        default='PLAIN',
        update=drawPlate
    )

    my_top_ends: bpy.props.EnumProperty(
        items=[('PLAIN', "Plain", ""), ('BEVEL', "Round", ""), ('SLANT', "Slanted", ""), ('CHAMFER', "Chamfered", "")],
        default='PLAIN',
        update=drawPlate
    )

    my_top_height: bpy.props.EnumProperty(
        items=[('3', "1.5mm", ""), ('4', "2mm", ""), ('5', "2.5mm", ""), ('6', "3mm", "")],
        default='4',
        update=drawPlate
    )

    drop_top_halfway: bpy.props.BoolProperty(
        name="Drop Half Way",
        description="Drop the top plate halfway into the main plate instead of sitting it fully on top",
        default=False,
        update=drawPlate
    )

    end_length: bpy.props.EnumProperty(
        items=[
            ('2', "2mm End Caps", ""),
            ('3', "3mm End Caps", ""),
            ('4', "4mm End Caps", ""),
            ('5', "5mm End Caps", ""),
            ('6', "6mm End Caps", ""),
        ],
        default='4',
        update=drawPlate
    )

    top_angles: bpy.props.EnumProperty(
        items=[("25", "1/4 Base Coverage", ""), ("50", "1/2 Base Coverage", ""), ("75", "3/4 Coverage", ""), ("100", "Full Coverage", "")],
        default="50",
        update=drawPlate
    )

    o_angles: bpy.props.EnumProperty(
        items=[("0", "90 Degrees", "90 Degrees"), ("1", "120 Degrees", "120 Degrees"), ("2", "135 Degrees", "135 Degrees")],
        default="0",
        update=drawPlate
    )

    angles: bpy.props.EnumProperty(
        items=[("25", "90 Degrees", "90 Degrees"), ("33", "120 Degrees", "120 Degrees"), ("41", "150 Degrees", "150 Degrees"), ("50", "180 Degrees", "180 Degrees")],
        default="41",
        update=drawPlate
    )

    my_item: bpy.props.EnumProperty(
        items=[
            ('PLATE', "Nameplate", ""),
            ('UPPERTEXT', "Upper Text", ""),
            ('MAINTEXT', "Main Text", ""),
            ('NURNIE_LEFT', "Left Nurnie", ""),
            ('NURNIE_RIGHT', "Right Nurnie", ""),
        ],
        default="PLATE",
        update=selectItem
    )

    my_newbase: bpy.props.EnumProperty(
        items=[("NEW", "NEW", "NEW"), ("IMPORT", "IMPORT", "IMPORT")],
        default="NEW",
    )

def register():
    bpy.utils.register_class(MyProperties)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MyProperties)

    bpy.types.Object.myZFloat = FloatProperty(
        name="<< Down / Up >>", description="Set the location on local Z axis",
        min=-100, max=100, soft_min=-10, soft_max=10, step=1, subtype='DISTANCE',
        get=get_locationZ, set=set_locationZ
    )
    bpy.types.Object.myYFloat = FloatProperty(
        name="<< Back / Forwards >>", description="Set the location on local Y axis",
        min=-100, max=100, soft_min=-10, soft_max=10, step=1, subtype='DISTANCE',
        get=get_locationY, set=set_locationY
    )
    bpy.types.Object.myNurnZFloat = FloatProperty(
        name="<< Back / Forwards >>", description="Set the location on local Z axis",
        min=-100, max=100, soft_min=-10, soft_max=10, step=1, subtype='DISTANCE',
        get=get_locationZ, set=set_locationZ
    )
    bpy.types.Object.myNurnYFloat = FloatProperty(
        name="<< Down / Up >>", description="Set the location on local Y axis",
        min=-100, max=100, soft_min=-10, soft_max=10, step=1, subtype='DISTANCE',
        get=get_locationY, set=set_locationY
    )


def unregister():
    for attr in ("myNurnYFloat", "myNurnZFloat", "myYFloat", "myZFloat"):
        if hasattr(bpy.types.Object, attr):
            delattr(bpy.types.Object, attr)

    if hasattr(bpy.types.Scene, "my_tool"):
        del bpy.types.Scene.my_tool

    bpy.utils.unregister_class(MyProperties)
