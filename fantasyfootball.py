bl_info = {
    "name": "Fantasy Football Addon",
    "author": "Kev Thomas",
    "version": (2, 1, 2),
    "blender": (4, 5, 0),
    "location": "View3D > UI > BloodBowl Tab",
    "description": "Adds Fantasy Football to the NamePlateGenerator",
    "category": "User Interface",
}

import bpy
import csv
import os
import json
from bpy.props import (
    StringProperty,
    CollectionProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
    PointerProperty,
)
from bpy.types import (
    Panel,
    Operator,
    PropertyGroup,
)

CONFIG_PATH = os.path.join(bpy.utils.user_resource('CONFIG'), "fantasyfootball_config.json")

def save_config(data):
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Failed to save config: {e}")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load config: {e}")
    return {"show_welcome": True}

def update_welcome_preference(self, context):
    save_config({"show_welcome": self.show_welcome})

def int_to_roman(n):
    val_map = [
        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]
    result = ""
    for val, sym in val_map:
        while n >= val:
            result += sym
            n -= val
    return result

def count_update(self, context):
    if self.count < 0:
        self.count = 0
    elif self.count > self.number_allowed:
        self.count = self.number_allowed

class WelcomeProperties(bpy.types.PropertyGroup):
    show_welcome: BoolProperty(
        name="Show Welcome",
        description="Show welcome message on startup",
        default=True,
        update=update_welcome_preference
    )

class TeamPosition(PropertyGroup):
    position_name: StringProperty(name="Position")
    number_allowed: IntProperty(name="Number Allowed")
    base_size: StringProperty(name="Base Size")
    count: IntProperty(name="Count", default=0, min=0, update=count_update)

class TeamEntry(PropertyGroup):
    name: StringProperty(name="Team Name")
    positions: CollectionProperty(type=TeamPosition)

class StoredPosition(PropertyGroup):
    text: StringProperty()

class CSVToolProperties(PropertyGroup):
    csv_path: StringProperty(name="CSV File Path", subtype='FILE_PATH')
    team_list: CollectionProperty(type=TeamEntry)
    active_team: StringProperty(name="Active Team", default="")
    show_team_section: BoolProperty(name="Show Team Selection", default=True)
    show_csv_section: BoolProperty(name="Show CSV Loader", default=True)
    stored_positions: CollectionProperty(type=StoredPosition)
    team_index: IntProperty(name="Team Index", default=0)

    number_display_mode: EnumProperty(
        name="Number Display Mode",
        description="Choose how to display positional numbers",
        items=[
            ('OFF', "OFF", "Do not display numbers"),
            ('NORMAL', "1, 2, 3", "Show standard numbers"),
            ('ROMAN', "I, II, III", "Show Roman numerals"),
        ],
        default='OFF'
    )
    capitalization_mode: EnumProperty(
        name="Capitalization",
        description="Display position names as lowercase or UPPERCASE",
        items=[
            ('UPPER', "POSITION", "Display as uppercase"),
            ('LOWER', "Position", "Display as lowercase"),
        ],
        default='LOWER'
    )
    stunty_base: EnumProperty(
        name="Stunty Base Size",
        items=[
            ('25', "25mm", "Use 25mm bases for Stunty"),
            ('32', "32mm", "Use 32mm bases for Stunty")
        ],
        default='25'
    )
    big_guy_base: EnumProperty(
        name="Big Guy Base Size",
        items=[
            ('32', "32mm", "Use 32mm bases for Big Guys"),
            ('40', "40mm", "Use 40mm bases for Big Guys")
        ],
        default='40'
    )

class OT_LoadCSV(Operator):
    bl_idname = "wm.load_csv"
    bl_label = "Load CSV"

    def execute(self, context):
        props = context.scene.csv_tool_props
        props.team_list.clear()
        props.active_team = ""
        if not props.csv_path or not os.path.exists(bpy.path.abspath(props.csv_path)):
            self.report({'ERROR'}, "Invalid or missing file path.")
            return {'CANCELLED'}

        with open(bpy.path.abspath(props.csv_path), newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if not row:
                    continue
                team = props.team_list.add()
                team.name = row[0]
                for i in range(1, len(row[1:]), 3):
                    if i + 2 < len(row):
                        pos = team.positions.add()
                        pos.position_name = row[i]
                        pos.number_allowed = int(row[i+1]) if row[i+1].isdigit() else 0
                        size_code = row[i+2].strip().upper()
                        if size_code == 'S':
                            pos.base_size = props.stunty_base
                        elif size_code == 'L':
                            pos.base_size = props.big_guy_base
                        else:
                            pos.base_size = '32'
                        pos.count = pos.number_allowed

        if props.team_list:
            props.active_team = props.team_list[0].name
        return {'FINISHED'}

class OT_SelectTeam(Operator):
    bl_idname = "wm.select_team"
    bl_label = "Select Team"
    team_name: StringProperty(default="")

    def execute(self, context):
        props = context.scene.csv_tool_props
        for team in props.team_list:
            if team.name == props.active_team:
                for pos in team.positions:
                    pos.count = 0
        for team in props.team_list:
            if team.name == self.team_name:
                for pos in team.positions:
                    pos.count = pos.number_allowed
        props.active_team = self.team_name
        return {'FINISHED'}

class OT_IncreaseCount(Operator):
    bl_idname = "csv.increase_count"
    bl_label = "Increase Count"
    pos_index: IntProperty(default=0)

    def execute(self, context):
        props = context.scene.csv_tool_props
        for team in props.team_list:
            if team.name == props.active_team:
                if 0 <= self.pos_index < len(team.positions):
                    pos = team.positions[self.pos_index]
                    if pos.count < pos.number_allowed:
                        pos.count += 1
        return {'FINISHED'}

class OT_DecreaseCount(Operator):
    bl_idname = "csv.decrease_count"
    bl_label = "Decrease Count"
    pos_index: IntProperty(default=0)

    def execute(self, context):
        props = context.scene.csv_tool_props
        for team in props.team_list:
            if team.name == props.active_team:
                if 0 <= self.pos_index < len(team.positions):
                    pos = team.positions[self.pos_index]
                    if pos.count > 0:
                        pos.count -= 1
        return {'FINISHED'}

class OT_ToggleTeamSection(Operator):
    bl_idname = "wm.toggle_team_section"
    bl_label = "Toggle Team Section"

    def execute(self, context):
        props = context.scene.csv_tool_props
        props.show_team_section = not props.show_team_section
        return {'FINISHED'}

class OT_StorePositions(Operator):
    bl_idname = "csv.store_positions"
    bl_label = "Generate Position List"

    def execute(self, context):
        props = context.scene.csv_tool_props
        props.stored_positions.clear()
        team = next((t for t in props.team_list if t.name == props.active_team), None)
        if not team:
            self.report({'WARNING'}, "No active team selected")
            return {'CANCELLED'}

        team_name = team.name.upper() if props.capitalization_mode == 'UPPER' else team.name
        props.stored_positions.add().text = f"Team: {team_name}"
        longest_entry = ""
        used_stunty = False

        for pos in team.positions:
            if pos.count == 0:
                continue
            name = pos.position_name.upper() if props.capitalization_mode == 'UPPER' else pos.position_name

            if pos.base_size == props.stunty_base:
                used_stunty = True

            if props.number_display_mode != 'OFF':
                if pos.count == 1 or pos.number_allowed == 1:
                    line = name
                    props.stored_positions.add().text = line
                    if len(line) > len(longest_entry):
                        longest_entry = line
                else:
                    for i in range(1, pos.count + 1):
                        num = int_to_roman(i) if props.number_display_mode == 'ROMAN' else str(i)
                        line = f"{name} {num}"
                        props.stored_positions.add().text = line
                        if len(line) > len(longest_entry):
                            longest_entry = line
            else:
                for _ in range(pos.count):
                    line = name
                    props.stored_positions.add().text = line
                    if len(line) > len(longest_entry):
                        longest_entry = line

        if longest_entry:
            props.stored_positions.add().text = f"Longest Entry: {longest_entry}"
            obj = bpy.data.objects.get("MAINTEXT")
            if obj and obj.type == 'FONT':
                for o in bpy.context.view_layer.objects:
                    o.select_set(False)
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                obj.data.body = longest_entry

        is_nameplate_loaded = "NAME_PLATE_GENERATOR_2" in bpy.context.preferences.addons
        status = "Nameplate Generator is ENABLED" if is_nameplate_loaded else "Nameplate Generator is NOT enabled"

        msg = "Positions stored. " + status
        if used_stunty:
            msg += " (Stunty base used in one or more positions.)"

        self.report({'INFO'}, msg)
        return {'FINISHED'}

class CSVToolPanel(Panel):
    bl_label = "Fantasy Football Addon"
    bl_idname = "VIEW3D_PT_csv_team_selector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BloodBowl Tab'

    def draw(self, context):
        layout = self.layout
        props = context.scene.csv_tool_props
        wm = context.window_manager
        welcome = wm.welcome_props

        if welcome.show_welcome:
            box = layout.box()
            box.label(text="👋 Welcome to Blood Bowl Tools")
            box.prop(welcome, "show_welcome", text="Don't show this again")

        box_csv = layout.box()
        box_csv.prop(props, "show_csv_section")
        if props.show_csv_section:
            box_csv.prop(props, "csv_path")
            box_csv.operator("wm.load_csv", icon='FILE_FOLDER')

        box_team = layout.box()
        box_team.prop(props, "show_team_section")
        if props.team_list and props.show_team_section:
            box_team.label(text="Select Team:")
            box_team.template_list("UI_UL_list", "team_list", props, "team_list", props, "team_index", rows=5)
            if 0 <= props.team_index < len(props.team_list):
                selected_team = props.team_list[props.team_index]
                row = box_team.row()
                op = row.operator("wm.select_team", text=f"Set Team: {selected_team.name}")
                op.team_name = selected_team.name

        box_pos = layout.box()
        for team in props.team_list:
            if team.name == props.active_team:
                box_pos.label(text=f"Positions in {team.name}:")
                for i, pos in enumerate(team.positions):
                    box_pos.label(text=f"{pos.position_name} ({pos.count}/{pos.number_allowed})")
                    row = box_pos.row(align=True)
                    row.operator("csv.decrease_count", text="-").pos_index = i
                    row.operator("csv.increase_count", text="+").pos_index = i

        box_actions = layout.box()
        box_actions.label(text="Positional Numbering:")
        box_actions.row().prop(props, "number_display_mode", expand=True)
        box_actions.label(text="Capitalization:")
        box_actions.row().prop(props, "capitalization_mode", expand=True)

        row = box_actions.row()
        col1 = row.column()
        col2 = row.column()

        col1.label(text="Stunty Base Size:")
        col1.prop(props, "stunty_base", expand=True)

        col2.label(text="Big Guy Base Size:")
        col2.prop(props, "big_guy_base", expand=True)
        box_actions.operator("csv.store_positions", icon="FILE_TICK")

classes = (
    WelcomeProperties,
    TeamPosition,
    TeamEntry,
    StoredPosition,
    CSVToolProperties,
    OT_LoadCSV,
    OT_SelectTeam,
    OT_IncreaseCount,
    OT_DecreaseCount,
    OT_ToggleTeamSection,
    OT_StorePositions,
    CSVToolPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.csv_tool_props = PointerProperty(type=CSVToolProperties)
    bpy.types.WindowManager.welcome_props = PointerProperty(type=WelcomeProperties)

    config = load_config()
    bpy.context.window_manager.welcome_props.show_welcome = config.get("show_welcome", True)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.csv_tool_props
    del bpy.types.WindowManager.welcome_props

#if __name__ == "__main__":
#    register()