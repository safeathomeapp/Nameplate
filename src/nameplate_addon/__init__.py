bl_info = {
    "name": "NamePlate Generator",
    "author": "Kev Thomas",
    "version": (2, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Name Plate",
    "description": "Adds a new NamePlate Object with user defined properties",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}

from . import operators
from . import properties
from . import ui


def register():
    properties.register()
    operators.register()
    ui.register()


def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()
