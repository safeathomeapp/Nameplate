import os

import bpy


_ICON_COLLECTION = None

_ICON_FILES = {
    "SQUARE": "icon_square_32.png",
    "CHAMFERED": "icon_chamfered_32.png",
    "SLANTED": "icon_slanted_32.png",
    "ROUNDED": "icon_rounded_32.png",
}


def _icons_dir():
    return os.path.join(os.path.dirname(__file__), "icons")


def register():
    global _ICON_COLLECTION

    if _ICON_COLLECTION is not None:
        return

    try:
        import bpy.utils.previews

        pcoll = bpy.utils.previews.new()
        icons_dir = _icons_dir()
        for icon_name, filename in _ICON_FILES.items():
            filepath = os.path.join(icons_dir, filename)
            if os.path.exists(filepath):
                pcoll.load(icon_name, filepath, 'IMAGE')
        _ICON_COLLECTION = pcoll
    except Exception:
        _ICON_COLLECTION = None


def unregister():
    global _ICON_COLLECTION

    if _ICON_COLLECTION is None:
        return

    try:
        import bpy.utils.previews

        bpy.utils.previews.remove(_ICON_COLLECTION)
    except Exception:
        pass

    _ICON_COLLECTION = None


def get_icon_id(icon_name):
    if _ICON_COLLECTION is None:
        return 0
    icon = _ICON_COLLECTION.get(icon_name)
    if icon is None:
        return 0
    return icon.icon_id
