ADDON_TAB = "Name Plate"
ADDON_ID = "nameplate"
MANAGED_TAG = "nameplate_managed"
ROLE_TAG = "nameplate_role"
MM_TO_SCENE_UNITS = 1.0

OBJECT_NAMES = {
    "base": "BASE",
    "path": "PATH",
    "empty": "EMPTY",
    "plate": "PLATE",
}

REFERENCE_ROLES = ("BASE", "EMPTY", "PATH", "PLATE")
CURVED_BASE_FAMILIES = {"CIRCLE", "OVAL", "SPECIAL"}
BASE_REFERENCE_HEIGHT_MM = 2.0
PLATE_THICKNESS_MM = 3.0
PLATE_DEPTH_RATIO = 0.3
PLATE_LENGTH_RATIO = 0.8
PLATE_BEND_MODIFIER_NAME = "PlateBend"

BASE_FAMILY_ITEMS = (
    ("CIRCLE", "Circle Bases", "Curved circular base presets"),
    ("OVAL", "Oval Bases", "Curved oval base presets"),
    ("SQUARE", "Square Bases", "Straight square base presets"),
    ("SPECIAL", "Special Bases", "Special preset workflows"),
)

WORKFLOW_MODE_ITEMS = (
    ("NEW", "New", "Start a new procedural nameplate"),
    ("IMPORT", "Import", "Align an imported plate to a base reference"),
)

BASE_PRESETS = {
    "CIRCLE": (
        ("25", "25mm", "25mm circle base"),
        ("32", "32mm", "32mm circle base"),
        ("40", "40mm", "40mm circle base"),
        ("50", "50mm", "50mm circle base"),
        ("60", "60mm", "60mm circle base"),
        ("80", "80mm", "80mm circle base"),
        ("100", "100mm", "100mm circle base"),
        ("130", "130mm", "130mm circle base"),
        ("160", "160mm", "160mm circle base"),
    ),
    "OVAL": (
        ("60x35", "60x35", "60x35 oval base"),
        ("75x42", "75x42", "75x42 oval base"),
        ("90x52", "90x52", "90x52 oval base"),
        ("105x70", "105x70", "105x70 oval base"),
        ("120x92", "120x92", "120x92 oval base"),
        ("150x95", "150x95", "150x95 oval base"),
        ("170x105", "170x105", "170x105 oval base"),
    ),
    "SQUARE": (
        ("25", "25mm", "25mm square base"),
        ("32", "32mm", "32mm square base"),
        ("40", "40mm", "40mm square base"),
        ("50", "50mm", "50mm square base"),
        ("60", "60mm", "60mm square base"),
        ("80", "80mm", "80mm square base"),
        ("100", "100mm", "100mm square base"),
        ("130", "130mm", "130mm square base"),
        ("160", "160mm", "160mm square base"),
    ),
    "SPECIAL": (
        ("70x25_BIKE", "70x25 40K Bike", "Special 70x25 bike base"),
        ("95x40_BIKE", "95x40 40K Bike", "Special 95x40 bike base"),
    ),
}

DEFAULT_SETTINGS = {
    "workflow_mode": "NEW",
    "base_family": "CIRCLE",
    "base_preset_circle": "32",
    "base_preset_oval": "90x52",
    "base_preset_square": "32",
    "base_preset_special": "70x25_BIKE",
    "status_message": "Phase 2B ready. Build creates BASE, EMPTY, conditional PATH, and PLATE.",
}
