#!/usr/bin/env python3
"""Script to add missing properties dock widget to tpc.ui file."""

import xml.etree.ElementTree as ET
from pathlib import Path

def fix_tpc_ui():
    ui_file = Path("Tools/HolocronToolset/src/ui/editors/tpc.ui")
    
    tree = ET.parse(ui_file)
    root = tree.getroot()
    
    # Find the MainWindow widget
    main_window = root.find(".//widget[@class='QMainWindow']")
    if main_window is None:
        print("Error: Could not find QMainWindow widget")
        return
    
    # Find the toolbar to add action after
    toolbar = main_window.find(".//widget[@class='QToolBar']")
    if toolbar is None:
        print("Error: Could not find toolbar")
        return
    
    # Find the txiDockWidget to insert properties dock before it
    txi_dock = main_window.find(".//widget[@class='QDockWidget'][@name='txiDockWidget']")
    if txi_dock is None:
        print("Error: Could not find txiDockWidget")
        return
    
    # Create properties dock widget
    properties_dock = ET.Element("widget", {"class": "QDockWidget", "name": "propertiesDockWidget"})
    
    # Add properties dock properties
    window_title = ET.SubElement(properties_dock, "property", {"name": "windowTitle"})
    ET.SubElement(window_title, "string").text = "Properties"
    
    features = ET.SubElement(properties_dock, "property", {"name": "features"})
    features_set = ET.SubElement(features, "set")
    features_set.text = "QDockWidget::DockWidgetMovable|QDockWidget::DockWidgetFloatable|QDockWidget::DockWidgetClosable"
    
    dock_area = ET.SubElement(properties_dock, "attribute", {"name": "dockWidgetArea"})
    ET.SubElement(dock_area, "number").text = "1"
    
    # Create contents widget
    contents_widget = ET.SubElement(properties_dock, "widget", {"class": "QWidget", "name": "propertiesDockWidgetContents"})
    properties_layout = ET.SubElement(contents_widget, "layout", {"class": "QVBoxLayout", "name": "propertiesLayout"})
    
    # Layout properties
    for prop_name, prop_value in [("spacing", "4"), ("leftMargin", "4"), ("topMargin", "4"), ("rightMargin", "4"), ("bottomMargin", "4")]:
        prop = ET.SubElement(properties_layout, "property", {"name": prop_name})
        ET.SubElement(prop, "number").text = prop_value
    
    # Create form layout
    form_layout_item = ET.SubElement(properties_layout, "item")
    form_layout = ET.SubElement(form_layout_item, "widget", {"class": "QFormLayout", "name": "propertiesFormLayout"})
    
    # Define form fields
    fields = [
        ("dimensions", "Dimensions:"),
        ("format", "Format:"),
        ("layers", "Layers:"),
        ("mipmaps", "Mipmaps:"),
        ("compressed", "Compressed:"),
        ("animated", "Animated:"),
        ("cubeMap", "Cube Map:"),
    ]
    
    row = 0
    for field_name, label_text in fields:
        # Label
        label_item = ET.SubElement(form_layout, "item", {"row": str(row), "column": "0"})
        label_widget = ET.SubElement(label_item, "widget", {"class": "QLabel", "name": f"{field_name}Label"})
        label_prop = ET.SubElement(label_widget, "property", {"name": "text"})
        ET.SubElement(label_prop, "string").text = label_text
        
        # Value
        value_item = ET.SubElement(form_layout, "item", {"row": str(row), "column": "1"})
        value_widget = ET.SubElement(value_item, "widget", {"class": "QLabel", "name": f"{field_name}Value"})
        value_prop = ET.SubElement(value_widget, "property", {"name": "text"})
        ET.SubElement(value_prop, "string").text = "—"
        
        row += 1
    
    # Alpha test field (with spinbox)
    label_item = ET.SubElement(form_layout, "item", {"row": str(row), "column": "0"})
    label_widget = ET.SubElement(label_item, "widget", {"class": "QLabel", "name": "alphaTestLabel"})
    label_prop = ET.SubElement(label_widget, "property", {"name": "text"})
    ET.SubElement(label_prop, "string").text = "Alpha Test:"
    
    value_item = ET.SubElement(form_layout, "item", {"row": str(row), "column": "1"})
    spinbox_widget = ET.SubElement(value_item, "widget", {"class": "QDoubleSpinBox", "name": "alphaTestSpinBox"})
    
    decimals = ET.SubElement(spinbox_widget, "property", {"name": "decimals"})
    ET.SubElement(decimals, "number").text = "2"
    
    minimum = ET.SubElement(spinbox_widget, "property", {"name": "minimum"})
    ET.SubElement(minimum, "double").text = "0.000000000000000"
    
    maximum = ET.SubElement(spinbox_widget, "property", {"name": "maximum"})
    ET.SubElement(maximum, "double").text = "1.000000000000000"
    
    single_step = ET.SubElement(spinbox_widget, "property", {"name": "singleStep"})
    ET.SubElement(single_step, "double").text = "0.010000000000000"
    
    value = ET.SubElement(spinbox_widget, "property", {"name": "value"})
    ET.SubElement(value, "double").text = "0.500000000000000"
    
    # Add spacer
    spacer_item = ET.SubElement(properties_layout, "item")
    spacer = ET.SubElement(spacer_item, "spacer", {"name": "propertiesVerticalSpacer"})
    orientation = ET.SubElement(spacer, "property", {"name": "orientation"})
    ET.SubElement(orientation, "enum").text = "Qt::Vertical"
    size_hint = ET.SubElement(spacer, "property", {"name": "sizeHint", "stdset": "0"})
    size = ET.SubElement(size_hint, "size")
    ET.SubElement(size, "width").text = "20"
    ET.SubElement(size, "height").text = "40"
    
    # Insert properties dock before txi dock
    # Find parent by searching for widget containing txi_dock
    for widget in main_window.iter():
        if txi_dock in list(widget):
            index = list(widget).index(txi_dock)
            widget.insert(index, properties_dock)
            break
    
    # Add actionToggleProperties to View menu
    view_menu = main_window.find(".//widget[@class='QMenu'][@name='menuView']")
    if view_menu is not None:
        # Find the separator or actionToggleTXIEditor
        txi_action = view_menu.find(".//addaction[@name='actionToggleTXIEditor']")
        if txi_action is not None:
            # Insert after txi action
            props_action = ET.Element("addaction", {"name": "actionToggleProperties"})
            for widget in main_window.iter():
                if txi_action in list(widget):
                    index = list(widget).index(txi_action)
                    widget.insert(index + 1, props_action)
                    break
    
    # Add actionToggleProperties to toolbar
    toolbar_txi = toolbar.find(".//addaction[@name='actionToggleTXIEditor']")
    if toolbar_txi is not None:
        props_action = ET.Element("addaction", {"name": "actionToggleProperties"})
        for widget in main_window.iter():
            if toolbar_txi in list(widget):
                index = list(widget).index(toolbar_txi)
                widget.insert(index + 1, props_action)
                break
    
    # Add actionToggleProperties action definition
    actions = main_window.find(".//action[@name='actionToggleTXIEditor']")
    if actions is not None:
        props_action_def = ET.Element("action", {"name": "actionToggleProperties"})
        
        text_prop = ET.SubElement(props_action_def, "property", {"name": "text"})
        ET.SubElement(text_prop, "string").text = "Toggle &amp;Properties"
        
        tooltip_prop = ET.SubElement(props_action_def, "property", {"name": "toolTip"})
        ET.SubElement(tooltip_prop, "string").text = "Show/hide properties panel"
        
        checkable_prop = ET.SubElement(props_action_def, "property", {"name": "checkable"})
        ET.SubElement(checkable_prop, "bool").text = "true"
        
        checked_prop = ET.SubElement(props_action_def, "property", {"name": "checked"})
        ET.SubElement(checked_prop, "bool").text = "true"
        
        # Insert after actionToggleTXIEditor
        for widget in main_window.iter():
            if actions in list(widget):
                index = list(widget).index(actions)
                widget.insert(index + 1, props_action_def)
                break
    
    # Write the modified tree back
    tree.write(ui_file, encoding="UTF-8", xml_declaration=True)
    print(f"Successfully updated {ui_file}")

if __name__ == "__main__":
    fix_tpc_ui()

