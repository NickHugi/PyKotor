#!/usr/bin/env python3
"""Script to expand translation dictionaries with all common strings found in toolset."""
from __future__ import annotations

import json
import re
from pathlib import Path

# Common strings found across toolset
COMMON_STRINGS = {
    # Error and status messages from main.py
    "Failed to extract some items.": "Failed to extract some items.",
    "Extraction successful.": "Extraction successful.",
    "Error Opening Save Editor": "Error Opening Save Editor",
    "Fix Corruption Complete": "Fix Corruption Complete",
    "No Corruption Found": "No Corruption Found",
    "No corrupted saves were found.": "No corrupted saves were found.",
    "Corruption Fixed": "Corruption Fixed",
    "Fix Failed": "Fix Failed",
    "This save is corrupted.\nRight click and press <i>'Fix savegame corruption'</i> to fix this.": "This save is corrupted.\nRight click and press <i>'Fix savegame corruption'</i> to fix this.",
    "Native (System Default)": "Native (System Default)",
    "ERF Editor": "ERF Editor",
    "Debug Reload": "Debug Reload",
    
    # Common widget strings
    "Find and Replace": "Find and Replace",
    "Replace All": "Replace All",
    "Type to filter...": "Type to filter...",
    "Type to search commands...": "Type to search commands...",
    "No matching commands": "No matching commands",
    "Enter expression to watch...": "Enter expression to watch...",
    "Find...": "Find...",
    "Replace...": "Replace...",
    "Find Previous (Shift+F3)": "Find Previous (Shift+F3)",
    "Find Next (F3)": "Find Next (F3)",
    "Close (Escape)": "Close (Escape)",
    "Match Case": "Match Case",
    "Match Whole Word": "Match Whole Word",
    "Use Regular Expression": "Use Regular Expression",
    
    # Dialog strings
    "Edit Camera": "Edit Camera",
    "Edit Creature": "Edit Creature",
    "Edit Door": "Edit Door",
    "Edit Encounter": "Edit Encounter",
    "Edit Placeable": "Edit Placeable",
    "Edit Sound": "Edit Sound",
    "Edit Store": "Edit Store",
    "Edit Trigger": "Edit Trigger",
    "Edit Waypoint": "Edit Waypoint",
    "Override the TLK with a custom entry.": "Override the TLK with a custom entry.",
    "Create a new entry in the TLK.": "Create a new entry in the TLK.",
    "Select a GitHub Repository File": "Select a GitHub Repository File",
    "Type to filter paths...": "Type to filter paths...",
    "You are rate limited.": "You are rate limited.",
    "Repository Not Found": "Repository Not Found",
    "Using Fork": "Using Fork",
    "No Forks Available": "No Forks Available",
    "Forks Load Error": "Forks Load Error",
    "No Selection": "No Selection",
    "No Fork Selected": "No Fork Selected",
    "Clone Successful": "Clone Successful",
    "Clone Failed": "Clone Failed",
    "Download Successful": "Download Successful",
    "Download Failed": "Download Failed",
    "File Selection": "File Selection",
    "Building Item Lists...": "Building Item Lists...",
    "Room Properties": "Room Properties",
    "Invalid Input": "Invalid Input",
    "Error": "Error",
    
    # Common action strings
    "OK": "OK",
    "Cancel": "Cancel",
    "Yes": "Yes",
    "No": "No",
    "Apply": "Apply",
    "Close": "Close",
    "Save": "Save",
    "Delete": "Delete",
    "Add": "Add",
    "Remove": "Remove",
    "Browse": "Browse",
    "Refresh": "Refresh",
    "Search": "Search",
    "Replace": "Replace",
    "Find": "Find",
    "Next": "Next",
    "Previous": "Previous",
    "Clear": "Clear",
    "Reset": "Reset",
    "Default": "Default",
    "Select": "Select",
    "Choose": "Choose",
    "Confirm": "Confirm",
    "Are you sure?": "Are you sure?",
    "Select File": "Select File",
    "Select Directory": "Select Directory",
    "Select Folder": "Select Folder",
    "Save File": "Save File",
    "Open File": "Open File",
    
    # Status messages
    "Loading...": "Loading...",
    "Saving...": "Saving...",
    "Processing...": "Processing...",
    "Completed": "Completed",
    "Failed": "Failed",
    "Success": "Success",
}

print(f"Found {len(COMMON_STRINGS)} common strings to add to translation dictionaries")

