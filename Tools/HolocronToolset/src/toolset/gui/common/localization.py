"""Localization system for Holocron Toolset.

Provides translation functionality for all user-facing strings in the toolset.
Supports multiple languages matching the KotOR game languages.
"""
from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from pykotor.common.language import Language

if TYPE_CHECKING:
    from typing_extensions import TypedDict


class ToolsetLanguage(IntEnum):
    """Language IDs for toolset localization. Matches official KotOR game languages."""

    ENGLISH = 0
    FRENCH = 1
    GERMAN = 2
    ITALIAN = 3
    SPANISH = 4
    POLISH = 5

    @classmethod
    def from_pykotor_language(cls, language: Language) -> ToolsetLanguage:
        """Convert PyKotor Language enum to ToolsetLanguage."""
        mapping = {
            Language.ENGLISH: ToolsetLanguage.ENGLISH,
            Language.FRENCH: ToolsetLanguage.FRENCH,
            Language.GERMAN: ToolsetLanguage.GERMAN,
            Language.ITALIAN: ToolsetLanguage.ITALIAN,
            Language.SPANISH: ToolsetLanguage.SPANISH,
            Language.POLISH: ToolsetLanguage.POLISH,
        }
        return mapping.get(language, ToolsetLanguage.ENGLISH)

    def get_display_name(self) -> str:
        """Get the display name for the language in its native form."""
        names = {
            ToolsetLanguage.ENGLISH: "English",
            ToolsetLanguage.FRENCH: "Français",
            ToolsetLanguage.GERMAN: "Deutsch",
            ToolsetLanguage.ITALIAN: "Italiano",
            ToolsetLanguage.SPANISH: "Español",
            ToolsetLanguage.POLISH: "Polski",
        }
        return names[self]

    def get_language_code(self) -> str:
        """Get the ISO 639-1 language code."""
        codes = {
            ToolsetLanguage.ENGLISH: "en",
            ToolsetLanguage.FRENCH: "fr",
            ToolsetLanguage.GERMAN: "de",
            ToolsetLanguage.ITALIAN: "it",
            ToolsetLanguage.SPANISH: "es",
            ToolsetLanguage.POLISH: "pl",
        }
        return codes[self]


# Translation dictionaries
_TRANSLATIONS: dict[ToolsetLanguage, dict[str, str]] = {
    ToolsetLanguage.ENGLISH: {
        # Main Window
        "Holocron Toolset": "Holocron Toolset",
        "File": "File",
        "Edit": "Edit",
        "Tools": "Tools",
        "Theme": "Theme",
        "Language": "Language",
        "Help": "Help",
        "New": "New",
        "Open": "Open",
        "Recent Files": "Recent Files",
        "Settings": "Settings",
        "Exit": "Exit",
        "Edit Talk Table": "Edit Talk Table",
        "Edit Journal": "Edit Journal",
        "Module Designer": "Module Designer",
        "Indoor Map Builder": "Indoor Map Builder",
        "KotorDiff": "KotorDiff",
        "TSLPatchData Editor": "TSLPatchData Editor",
        "File Search": "File Search",
        "Clone Module": "Clone Module",
        "About": "About",
        "Instructions": "Instructions",
        "Check For Updates": "Check For Updates",
        "Discord": "Discord",
        "Holocron Toolset": "Holocron Toolset",
        "KOTOR Community Portal": "KOTOR Community Portal",
        "Deadly Stream": "Deadly Stream",
        # Resource types
        "Core": "Core",
        "Saves": "Saves",
        "Modules": "Modules",
        "Override": "Override",
        "Textures": "Textures",
        "Open Selected": "Open Selected",
        "Extract Selected": "Extract Selected",
        "TPC": "TPC",
        "Decompile": "Decompile",
        "Extract TXI": "Extract TXI",
        "MDL": "MDL",
        "Extract Textures": "Extract Textures",
        "Open Save Editor": "Open Save Editor",
        "Fix Corruption": "Fix Corruption",
        "Designer": "Designer",
        # Dialog/Editor types
        "Dialog": "Dialog",
        "Creature": "Creature",
        "Item": "Item",
        "Door": "Door",
        "Placeable": "Placeable",
        "Merchant": "Merchant",
        "Encounter": "Encounter",
        "Trigger": "Trigger",
        "Waypoint": "Waypoint",
        "Sound": "Sound",
        "Script": "Script",
        "TalkTable": "TalkTable",
        "GFF": "GFF",
        "ERF": "ERF",
        "TXT": "TXT",
        "SSF": "SSF",
        # Tooltips
        "Open the selected save in the Save Editor": "Open the selected save in the Save Editor",
        "Fixes all possible save corruption in all saves": "Fixes all possible save corruption in all saves",
        "Decompile feature is not available.": "Decompile feature is not available.",
        # Language selection
        "English": "English",
        "Français": "Français",
        "Deutsch": "Deutsch",
        "Italiano": "Italiano",
        "Español": "Español",
        "Polski": "Polski",
        # Common messages
        "Failed to extract some items.": "Failed to extract some items.",
        "Failed to save {count} files!": "Failed to save {count} files!",
        "Extraction successful.": "Extraction successful.",
        "Successfully saved {count} files to {path}": "Successfully saved {count} files to {path}",
        "Error Opening Save Editor": "Error Opening Save Editor",
        "Failed to open save editor:\n{error}": "Failed to open save editor:\n{error}",
        "Fix Corruption Complete": "Fix Corruption Complete",
        "Fixed corruption in {count} save(s).": "Fixed corruption in {count} save(s).",
        "Failed to fix {count} save(s).": "Failed to fix {count} save(s).",
        "No Corruption Found": "No Corruption Found",
        "No corrupted saves were found.": "No corrupted saves were found.",
        "Corruption Fixed": "Corruption Fixed",
        "Successfully fixed corruption in save:\n{name}": "Successfully fixed corruption in save:\n{name}",
        "Fix Failed": "Fix Failed",
        "Failed to fix corruption in save:\n{name}": "Failed to fix corruption in save:\n{name}",
        "This save is corrupted.\nRight click and press <i>'Fix savegame corruption'</i> to fix this.": "This save is corrupted.\nRight click and press <i>'Fix savegame corruption'</i> to fix this.",
        "Native (System Default)": "Native (System Default)",
        "ERF Editor": "ERF Editor",
        "Debug Reload": "Debug Reload",
        # Error messages
        "Error": "Error",
        "Warning": "Warning",
        "Information": "Information",
        "Question": "Question",
        # Common buttons/actions
        "OK": "OK",
        "Cancel": "Cancel",
        "Yes": "Yes",
        "No": "No",
        "Apply": "Apply",
        "Close": "Close",
        "Save": "Save",
        "Open": "Open",
        "Delete": "Delete",
        "Edit": "Edit",
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
        # Common dialogs
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
        # File dialogs
        "Extract to folder": "Extract to folder",
        "Select the game directory for {name}": "Select the game directory for {name}",
        "Save extracted {type} '{name}' as...": "Save extracted {type} '{name}' as...",
        "An error occurred while fixing corruption:\n{error}": "An error occurred while fixing corruption:\n{error}",
        # NSS Editor strings
        "Decompile or Download": "Decompile or Download",
        "Would you like to decompile this script, or download it from <a href='{url}'>Vanilla Source Repository</a>?": "Would you like to decompile this script, or download it from <a href='{url}'>Vanilla Source Repository</a>?",
        "Download": "Download",
        # Find/Replace widget strings
        "Find:": "Find:",
        "Replace:": "Replace:",
        # Theme Manager strings
        "Theme not found": "Theme not found",
        "QDarkStyle is not installed in this environment.": "QDarkStyle is not installed in this environment.",
        # Find/Replace widget
        "Find:": "Find:",
        "Replace:": "Replace:",
        # NSS Editor
        "Decompile or Download": "Decompile or Download",
        "Would you like to decompile this script, or download it from <a href='{url}'>Vanilla Source Repository</a>?": "Would you like to decompile this script, or download it from <a href='{url}'>Vanilla Source Repository</a>?",
        # Window.py messages
        "Failed to get the file data.": "Failed to get the file data.",
        "An error occurred while attempting to read the data of the file.": "An error occurred while attempting to read the data of the file.",
        "Cannot decompile NCS without an installation active": "Cannot decompile NCS without an installation active",
        "Please select an installation from the dropdown before loading an NCS.": "Please select an installation from the dropdown before loading an NCS.",
        "Failed to open file": "Failed to open file",
        "The selected file format '{format}' is not yet supported.": "The selected file format '{format}' is not yet supported.",
        "An unexpected error has occurred": "An unexpected error has occurred",
        # load_from_location_result.py messages
        "Nonexistent files found.": "Nonexistent files found.",
        "The following {count} files no longer exist:": "The following {count} files no longer exist:",
        "Errors occurred.": "Errors occurred.",
        "The following {count} files threw errors:": "The following {count} files threw errors:",
        "Show detailed": "Show detailed",
        "Stat attribute not expected format": "Stat attribute not expected format",
        "Failed to parse {column} ({attr}): {val}<br><br>{error}": "Failed to parse {column} ({attr}): {val}<br><br>{error}",
        "Exception": "Exception",
        "An error occurred: {error}": "An error occurred: {error}",
        # GitHub Selector strings
        "Please select the correct script path or enter manually:": "Please select the correct script path or enter manually:",
        "Select Fork:": "Select Fork:",
        "GitHub Repository": "GitHub Repository",
        "Clone Repository": "Clone Repository",
        "You have submitted too many requests to github's api, check the status bar at the bottom.": "You have submitted too many requests to github's api, check the status bar at the bottom.",
        "The repository '{owner}/{repo}' had an unexpected error:<br><br>{error}": "The repository '{owner}/{repo}' had an unexpected error:<br><br>{error}",
        "The main repository is not available. Using the fork: {fork}": "The main repository is not available. Using the fork: {fork}",
        "No forks are available to load.": "No forks are available to load.",
        "Failed to load forks: {error}": "Failed to load forks: {error}",
        "You must select a file.": "You must select a file.",
        "Please select a fork to clone.": "Please select a fork to clone.",
        "Repository {fork} cloned successfully.": "Repository {fork} cloned successfully.",
        "Failed to clone repository: {error}": "Failed to clone repository: {error}",
        "Open in Web Browser": "Open in Web Browser",
        "Copy URL": "Copy URL",
        "Downloaded {filename} to {path}": "Downloaded {filename} to {path}",
        "Failed to download the file content.": "Failed to download the file content.",
        "Failed to download {name}: {error}": "Failed to download {name}: {error}",
        # Code Editor strings
        "Replaced {count} occurrences": "Replaced {count} occurrences",
        # Command Palette strings
        "{language} - {name} - Localized String Editor": "{language} - {name} - Localized String Editor",
        # LYT Dialogs strings
        "Model:": "Model:",
        "Position:": "Position:",
        "X:": "X:",
        "Y:": "Y:",
        "Z:": "Z:",
        "Model name cannot be empty.": "Model name cannot be empty.",
        "Failed to update room properties: {error}": "Failed to update room properties: {error}",
        # GFF Editor strings
        "Invalid action attempted": "Invalid action attempted",
        "Cannot remove the top-level [ROOT] item.": "Cannot remove the top-level [ROOT] item.",
        "Select a TLK file": "Select a TLK file",
        # TLK Editor strings
        "No resources found": "No resources found",
        "There are no GFFs that reference this tlk entry (stringref {stringref})": "There are no GFFs that reference this tlk entry (stringref {stringref})",
        "{count} results for stringref '{stringref}' in {path}": "{count} results for stringref '{stringref}' in {path}",
        # Settings Dialog strings
        "Reset All Settings": "Reset All Settings",
        "Are you sure you want to reset all settings to their default values? This action cannot be undone.": "Are you sure you want to reset all settings to their default values? This action cannot be undone.",
        "Settings Reset": "Settings Reset",
        "All settings have been cleared and reset to their default values.": "All settings have been cleared and reset to their default values.",
        # Editor Help Dialog strings
        "Help - {filename}": "Help - {filename}",
        "Help File Not Found": "Help File Not Found",
        "Could not find help file: <code>{filename}</code>": "Could not find help file: <code>{filename}</code>",
        "Expected location: <code>{path}</code>": "Expected location: <code>{path}</code>",
        "Wiki path: <code>{path}</code>": "Wiki path: <code>{path}</code>",
        # UTI Editor strings
        "Reset this custom tag so it matches the resref": "Reset this custom tag so it matches the resref",
        # UTD Editor strings
        "This widget is only available in KOTOR II.": "This widget is only available in KOTOR II.",
        # UTP Editor strings
        "Total Items: {count}": "Total Items: {count}",
        # JRL Editor strings
        "The game multiplies the value set here by 1000 to calculate actual XP to award.": "The game multiplies the value set here by 1000 to calculate actual XP to award.",
        "'{file}.2da' is missing from your installation. Please reinstall your game, this should be in the read-only bifs.": "'{file}.2da' is missing from your installation. Please reinstall your game, this should be in the read-only bifs.",
        # TPC Editor strings
        "No Texture": "No Texture",
        "No texture loaded to copy.": "No texture loaded to copy.",
        "Texture copied to clipboard": "Texture copied to clipboard",
        "Copy Failed": "Copy Failed",
        "Failed to copy texture:\n{error}": "Failed to copy texture:\n{error}",
        "No Image": "No Image",
        "Clipboard does not contain an image.": "Clipboard does not contain an image.",
        "Texture pasted from clipboard": "Texture pasted from clipboard",
        "Paste Failed": "Paste Failed",
        "Failed to paste texture:\n{error}": "Failed to paste texture:\n{error}",
        # MDL Editor strings
        "Could not find the '{name}' MDL/MDX": "Could not find the '{name}' MDL/MDX",
        # Savegame Editor strings
        "Error Loading Save": "Error Loading Save",
        "Failed to load save game:\n{error}": "Failed to load save game:\n{error}",
        "No Save Loaded": "No Save Loaded",
        "No save game is currently loaded.": "No save game is currently loaded.",
        "Save game saved successfully": "Save game saved successfully",
        "Error Saving": "Error Saving",
        "Failed to save game:\n{error}": "Failed to save game:\n{error}",
        # LYT Editor strings
        "Failed to load LYT: {error}": "Failed to load LYT: {error}",
        # GIT Editor strings
        "Confirm Exit": "Confirm Exit",
        "Really quit the GIT editor? You may lose unsaved changes.": "Really quit the GIT editor? You may lose unsaved changes.",
        # PTH Editor strings
        "Layout not found": "Layout not found",
        "PTHEditor requires {resref}.lyt in order to load '{resref}.{restype}', but it could not be found.": "PTHEditor requires {resref}.lyt in order to load '{resref}.{restype}', but it could not be found.",
        "Add Node": "Add Node",
        "Copy XY coords": "Copy XY coords",
        "Remove Node": "Remove Node",
        # LIP Editor strings
        "Path to the WAV audio file": "Path to the WAV audio file",
        "Audio File:": "Audio File:",
        "Load Audio": "Load Audio",
        "Load a WAV audio file (Ctrl+O)": "Load a WAV audio file (Ctrl+O)",
        "Duration:": "Duration:",
        "Duration of the loaded audio file": "Duration of the loaded audio file",
        "List of keyframes (right-click for options)": "List of keyframes (right-click for options)",
        # DLG Editor strings
        "All Tips": "All Tips",
        # Debug Watch Widget strings
        "Enter expression to watch...": "Enter expression to watch...",
        "Add Watch": "Add Watch",
        # Test Config Widget strings
        "OBJECT_INVALID (default: 0)": "OBJECT_INVALID (default: 0)",
        "GetLastAttacker():": "GetLastAttacker():",
        "GetLastPerceived():": "GetLastPerceived():",
        "OBJECT_SELF (default: 1)": "OBJECT_SELF (default: 1)",
        "GetEventCreator():": "GetEventCreator():",
        "GetEventTarget():": "GetEventTarget():",
        "Entry Point: StartingConditional()": "Entry Point: StartingConditional()",
        "Entry Point: main()": "Entry Point: main()",
        "Configure Test Run": "Configure Test Run",
        # Combobox strings
        "FilterComboBox Test": "FilterComboBox Test",
        # Tree Widget strings
        "What's This?": "What's This?",
        "Enter 'What's This?' mode.": "Enter 'What's This?' mode.",
        # Installations Widget strings
        "New": "New",
        # Insert Instance Dialog strings
        "Choose an instance": "Choose an instance",
        "You must choose an instance, use the radial buttons to determine where/how to create the GIT instance.": "You must choose an instance, use the radial buttons to determine where/how to create the GIT instance.",
        # Resource Comparison Dialog strings
        "Compare: {name}.{ext}": "Compare: {name}.{ext}",
        "<b>Left:</b>": "<b>Left:</b>",
        "<b>Right:</b>": "<b>Right:</b>",
        "[Not selected]": "[Not selected]",
        # Indoor Settings Dialog strings
        "[None]": "[None]",
        # Select Update Dialog strings
        "Include Pre-releases": "Include Pre-releases",
        "Fetch Releases": "Fetch Releases",
        "Select Fork:": "Select Fork:",
        "Select Release:": "Select Release:",
        "Install Selected": "Install Selected",
        "Update to Latest": "Update to Latest",
        "Holocron Toolset Current Version: {version}": "Holocron Toolset Current Version: {version}",
        "Select a release": "Select a release",
        "No release selected, select one first.": "No release selected, select one first.",
        "No asset found": "No asset found",
        "There are no binaries available for download for release '{tag}'.": "There are no binaries available for download for release '{tag}'.",
        # TSLPatchData Editor strings
        "TSLPatchData Editor - Create HoloPatcher Mod": "TSLPatchData Editor - Create HoloPatcher Mod",
        "<b>TSLPatchData Folder:</b>": "<b>TSLPatchData Folder:</b>",
        "Browse...": "Browse...",
        "Create New": "Create New",
        "<b>Files to Package:</b>": "<b>Files to Package:</b>",
        "File": "File",
        "Status": "Status",
        "Add File": "Add File",
        "Select Files to Add": "Select Files to Add",
        "Added": "Added",
        "Scan from Diff": "Scan from Diff",
        "This will scan a KotorDiff results file and automatically populate files.\n\nNot yet implemented.": "This will scan a KotorDiff results file and automatically populate files.\n\nNot yet implemented.",
        "Select Scripts (.ncs)": "Select Scripts (.ncs)",
        "Not Found": "Not Found",
        "dialog.tlk not found in installation.": "dialog.tlk not found in installation.",
        "No Installation": "No Installation",
        "No installation loaded.": "No installation loaded.",
        "Created": "Created",
        "New tslpatchdata folder created at:\n{path}": "New tslpatchdata folder created at:\n{path}",
        "Saved": "Saved",
        "Configuration saved to:\n{path}": "Configuration saved to:\n{path}",
        "Generated": "Generated",
        "TSLPatchData generated at:\n{path}\n\nYou can now distribute this folder with HoloPatcher/TSLPatcher.": "TSLPatchData generated at:\n{path}\n\nYou can now distribute this folder with HoloPatcher/TSLPatcher.",
        # Module Designer strings
        "Module Designer": "Module Designer",
        "Really quit the module designer? You may lose unsaved changes.": "Really quit the module designer? You may lose unsaved changes.",
        # Indoor Map Builder strings
        "No installation - Map Builder": "No installation - Map Builder",
        "{name} - Map Builder": "{name} - Map Builder",
        "{path} - {name} - Map Builder": "{path} - {name} - Map Builder",
        "No Kits Available": "No Kits Available",
        "No kits were detected, would you like to open the Kit downloader?": "No kits were detected, would you like to open the Kit downloader?",
        "Failed to load file": "Failed to load file",
        "{error}": "{error}",
        # KotorDiff Window strings
        "KotorDiff - Holocron Toolset": "KotorDiff - Holocron Toolset",
        "Path to tslpatchdata folder": "Path to tslpatchdata folder",
        # Audio Player strings
        "{name}.{ext} - Audio Player": "{name}.{ext} - Audio Player",
        # Update Dialog strings (run_progress_dialog function)
        "Operation Progress": "Operation Progress",
        # Generic File Saver strings
        "Existing files/folders found.": "Existing files/folders found.",
        "The following {count} files and folders already exist in the selected folder.<br><br>How would you like to handle this?": "The following {count} files and folders already exist in the selected folder.<br><br>How would you like to handle this?",
        "Overwrite": "Overwrite",
        "Auto-Rename": "Auto-Rename",
        "Failed to extract files to disk.": "Failed to extract files to disk.",
        "{count} files FAILED to to be saved<br><br>Press 'show details' for information.": "{count} files FAILED to to be saved<br><br>Press 'show details' for information.",
        # AsyncLoader/ProgressDialog strings
        "Initializing...": "Initializing...",
        "Time remaining: --/--": "Time remaining: --/--",
        "Downloading... {progress}%": "Downloading... {progress}%",
        "Time remaining: {time}": "Time remaining: {time}",
        # Help Window strings
        "An unexpected error occurred while parsing the help booklet.": "An unexpected error occurred while parsing the help booklet.",
        "Failed to open help file": "Failed to open help file",
        "Could not access '{filepath}'.\n{error}": "Could not access '{filepath}'.\n{error}",
        "Help book missing": "Help book missing",
        "You do not seem to have a valid help booklet downloaded, would you like to download it?": "You do not seem to have a valid help booklet downloaded, would you like to download it?",
        "Update available": "Update available",
        "A newer version of the help book is available for download, would you like to download it?": "A newer version of the help book is available for download, would you like to download it?",
        "Download newer help files...": "Download newer help files...",
        # Update Manager strings
        "Unable to fetch latest version ({type})": "Unable to fetch latest version ({type})",
        "Check if you are connected to the internet.\nError: {error}": "Check if you are connected to the internet.\nError: {error}",
        "Version is up to date": "Version is up to date",
        "You are running the latest {version_str}version ({version}).": "You are running the latest {version_str}version ({version}).",
        "Auto-Update": "Auto-Update",
        "Choose Update": "Choose Update",
        "Your toolset version {version} is outdated.": "Your toolset version {version} is outdated.",
        "A new toolset {beta_str}version ({new_version}) is available for <a href='{link}'>download</a>.<br><br>{notes}": "A new toolset {beta_str}version ({new_version}) is available for <a href='{link}'>download</a>.<br><br>{notes}",
        "Details": "Details",
        "Ignore": "Ignore",
    },
    ToolsetLanguage.FRENCH: {
        # Main Window
        "Holocron Toolset": "Holocron Toolset",
        "File": "Fichier",
        "Edit": "Modifier",
        "Tools": "Outils",
        "Theme": "Thème",
        "Language": "Langue",
        "Help": "Aide",
        "New": "Nouveau",
        "Open": "Ouvrir",
        "Recent Files": "Fichiers récents",
        "Settings": "Paramètres",
        "Exit": "Quitter",
        "Edit Talk Table": "Modifier la table de conversation",
        "Edit Journal": "Modifier le journal",
        "Module Designer": "Concepteur de modules",
        "Indoor Map Builder": "Constructeur de cartes intérieures",
        "KotorDiff": "KotorDiff",
        "TSLPatchData Editor": "Éditeur TSLPatchData",
        "File Search": "Recherche de fichiers",
        "Clone Module": "Cloner le module",
        "About": "À propos",
        "Instructions": "Instructions",
        "Check For Updates": "Vérifier les mises à jour",
        "Discord": "Discord",
        "Holocron Toolset": "Holocron Toolset",
        "KOTOR Community Portal": "Portail communautaire KOTOR",
        "Deadly Stream": "Deadly Stream",
        # Resource types
        "Core": "Principal",
        "Saves": "Sauvegardes",
        "Modules": "Modules",
        "Override": "Remplacement",
        "Textures": "Textures",
        "Open Selected": "Ouvrir la sélection",
        "Extract Selected": "Extraire la sélection",
        "TPC": "TPC",
        "Decompile": "Décompiler",
        "Extract TXI": "Extraire TXI",
        "MDL": "MDL",
        "Extract Textures": "Extraire les textures",
        "Open Save Editor": "Ouvrir l'éditeur de sauvegarde",
        "Fix Corruption": "Réparer la corruption",
        "Designer": "Concepteur",
        # Dialog/Editor types
        "Dialog": "Dialogue",
        "Creature": "Créature",
        "Item": "Objet",
        "Door": "Porte",
        "Placeable": "Placeable",
        "Merchant": "Marchand",
        "Encounter": "Rencontre",
        "Trigger": "Déclencheur",
        "Waypoint": "Point de passage",
        "Sound": "Son",
        "Script": "Script",
        "TalkTable": "Table de conversation",
        "GFF": "GFF",
        "ERF": "ERF",
        "TXT": "TXT",
        "SSF": "SSF",
        # Tooltips
        "Open the selected save in the Save Editor": "Ouvrir la sauvegarde sélectionnée dans l'éditeur de sauvegarde",
        "Fixes all possible save corruption in all saves": "Répare toute corruption possible dans toutes les sauvegardes",
        "Decompile feature is not available.": "La fonction de décompilation n'est pas disponible.",
        # Language selection
        "English": "Anglais",
        "Français": "Français",
        "Deutsch": "Allemand",
        "Italiano": "Italien",
        "Español": "Espagnol",
        "Polski": "Polonais",
        # Common messages
        "Failed to extract some items.": "Échec de l'extraction de certains éléments.",
        "Failed to save {count} files!": "Échec de l'enregistrement de {count} fichier(s) !",
        "Extraction successful.": "Extraction réussie.",
        "Successfully saved {count} files to {path}": "Enregistrement réussi de {count} fichier(s) dans {path}",
        "Error Opening Save Editor": "Erreur lors de l'ouverture de l'éditeur de sauvegarde",
        "Failed to open save editor:\n{error}": "Échec de l'ouverture de l'éditeur de sauvegarde :\n{error}",
        "Fix Corruption Complete": "Réparation de la corruption terminée",
        "Fixed corruption in {count} save(s).": "Corruption réparée dans {count} sauvegarde(s).",
        "Failed to fix {count} save(s).": "Échec de la réparation de {count} sauvegarde(s).",
        "No Corruption Found": "Aucune corruption trouvée",
        "No corrupted saves were found.": "Aucune sauvegarde corrompue n'a été trouvée.",
        "Corruption Fixed": "Corruption réparée",
        "Successfully fixed corruption in save:\n{name}": "Corruption réparée avec succès dans la sauvegarde :\n{name}",
        "Fix Failed": "Échec de la réparation",
        "Failed to fix corruption in save:\n{name}": "Échec de la réparation de la corruption dans la sauvegarde :\n{name}",
        "This save is corrupted.\nRight click and press <i>'Fix savegame corruption'</i> to fix this.": "Cette sauvegarde est corrompue.\nCliquez avec le bouton droit et appuyez sur <i>'Fix savegame corruption'</i> pour corriger cela.",
        "Native (System Default)": "Natif (par défaut du système)",
        "ERF Editor": "Éditeur ERF",
        "Debug Reload": "Rechargement de débogage",
        # Error messages
        "Error": "Erreur",
        "Warning": "Avertissement",
        "Information": "Information",
        "Question": "Question",
        # Common buttons/actions
        "OK": "OK",
        "Cancel": "Annuler",
        "Yes": "Oui",
        "No": "Non",
        "Apply": "Appliquer",
        "Close": "Fermer",
        "Save": "Enregistrer",
        "Delete": "Supprimer",
        "Add": "Ajouter",
        "Remove": "Retirer",
        "Browse": "Parcourir",
        "Refresh": "Actualiser",
        "Search": "Rechercher",
        "Replace": "Remplacer",
        "Find": "Trouver",
        "Next": "Suivant",
        "Previous": "Précédent",
        "Clear": "Effacer",
        "Reset": "Réinitialiser",
        "Default": "Par défaut",
        # Common dialogs
        "Select": "Sélectionner",
        "Choose": "Choisir",
        "Confirm": "Confirmer",
        "Are you sure?": "Êtes-vous sûr ?",
        "Select File": "Sélectionner un fichier",
        "Select Directory": "Sélectionner un répertoire",
        "Select Folder": "Sélectionner un dossier",
        "Save File": "Enregistrer le fichier",
        "Open File": "Ouvrir un fichier",
        # Status messages
        "Loading...": "Chargement...",
        "Saving...": "Enregistrement...",
        "Processing...": "Traitement...",
        "Completed": "Terminé",
        "Failed": "Échec",
        "Success": "Succès",
        # File dialogs
        "Extract to folder": "Extraire dans le dossier",
        "Select the game directory for {name}": "Sélectionner le répertoire du jeu pour {name}",
        "Save extracted {type} '{name}' as...": "Enregistrer le {type} extrait '{name}' sous...",
        "An error occurred while fixing corruption:\n{error}": "Une erreur s'est produite lors de la réparation de la corruption :\n{error}",
    },
    ToolsetLanguage.GERMAN: {
        # Main Window
        "Holocron Toolset": "Holocron Toolset",
        "File": "Datei",
        "Edit": "Bearbeiten",
        "Tools": "Werkzeuge",
        "Theme": "Design",
        "Language": "Sprache",
        "Help": "Hilfe",
        "New": "Neu",
        "Open": "Öffnen",
        "Recent Files": "Zuletzt verwendet",
        "Settings": "Einstellungen",
        "Exit": "Beenden",
        "Edit Talk Table": "Gesprächstabelle bearbeiten",
        "Edit Journal": "Tagebuch bearbeiten",
        "Module Designer": "Modul-Designer",
        "Indoor Map Builder": "Karten-Editor",
        "KotorDiff": "KotorDiff",
        "TSLPatchData Editor": "TSLPatchData Editor",
        "File Search": "Dateisuche",
        "Clone Module": "Modul klonen",
        "About": "Über",
        "Instructions": "Anleitung",
        "Check For Updates": "Auf Updates prüfen",
        "Discord": "Discord",
        "Holocron Toolset": "Holocron Toolset",
        "KOTOR Community Portal": "KOTOR Community Portal",
        "Deadly Stream": "Deadly Stream",
        # Resource types
        "Core": "Kern",
        "Saves": "Speicherstände",
        "Modules": "Module",
        "Override": "Überschreiben",
        "Textures": "Texturen",
        "Open Selected": "Ausgewählte öffnen",
        "Extract Selected": "Ausgewählte extrahieren",
        "TPC": "TPC",
        "Decompile": "Dekompilieren",
        "Extract TXI": "TXI extrahieren",
        "MDL": "MDL",
        "Extract Textures": "Texturen extrahieren",
        "Open Save Editor": "Speichereditor öffnen",
        "Fix Corruption": "Korruption reparieren",
        "Designer": "Designer",
        # Dialog/Editor types
        "Dialog": "Dialog",
        "Creature": "Kreatur",
        "Item": "Gegenstand",
        "Door": "Tür",
        "Placeable": "Platzierbar",
        "Merchant": "Händler",
        "Encounter": "Begegnung",
        "Trigger": "Auslöser",
        "Waypoint": "Wegpunkt",
        "Sound": "Ton",
        "Script": "Skript",
        "TalkTable": "Gesprächstabelle",
        "GFF": "GFF",
        "ERF": "ERF",
        "TXT": "TXT",
        "SSF": "SSF",
        # Tooltips
        "Open the selected save in the Save Editor": "Ausgewählten Speicherstand im Speichereditor öffnen",
        "Fixes all possible save corruption in all saves": "Repariert alle möglichen Speicherkorruptionen in allen Speicherständen",
        "Decompile feature is not available.": "Dekompilierungsfunktion ist nicht verfügbar.",
        # Language selection
        "English": "Englisch",
        "Français": "Französisch",
        "Deutsch": "Deutsch",
        "Italiano": "Italienisch",
        "Español": "Spanisch",
        "Polski": "Polnisch",
        # Common messages
        "Failed to extract some items.": "Fehler beim Extrahieren einiger Elemente.",
        "Failed to save {count} files!": "Fehler beim Speichern von {count} Datei(en)!",
        "Extraction successful.": "Extrahierung erfolgreich.",
        "Successfully saved {count} files to {path}": "Erfolgreich {count} Datei(en) in {path} gespeichert",
        "Error Opening Save Editor": "Fehler beim Öffnen des Speichereditors",
        "Failed to open save editor:\n{error}": "Fehler beim Öffnen des Speichereditors:\n{error}",
        "Fix Corruption Complete": "Korruptionsreparatur abgeschlossen",
        "Fixed corruption in {count} save(s).": "Korruption in {count} Speicherstand/Speicherständen repariert.",
        "Failed to fix {count} save(s).": "Fehler beim Reparieren von {count} Speicherstand/Speicherständen.",
        "No Corruption Found": "Keine Korruption gefunden",
        "No corrupted saves were found.": "Es wurden keine korrupten Speicherstände gefunden.",
        "Corruption Fixed": "Korruption repariert",
        "Successfully fixed corruption in save:\n{name}": "Korruption erfolgreich in Speicherstand repariert:\n{name}",
        "Fix Failed": "Reparatur fehlgeschlagen",
        "Failed to fix corruption in save:\n{name}": "Fehler beim Reparieren der Korruption im Speicherstand:\n{name}",
        "This save is corrupted.\nRight click and press <i>'Fix savegame corruption'</i> to fix this.": "Dieser Speicherstand ist korrupt.\nRechtsklicken und <i>'Fix savegame corruption'</i> drücken, um dies zu beheben.",
        "Native (System Default)": "Nativ (Systemstandard)",
        "ERF Editor": "ERF-Editor",
        "Debug Reload": "Debug-Neuladen",
        # Error messages
        "Error": "Fehler",
        "Warning": "Warnung",
        "Information": "Information",
        "Question": "Frage",
        # Common buttons/actions
        "OK": "OK",
        "Cancel": "Abbrechen",
        "Yes": "Ja",
        "No": "Nein",
        "Apply": "Anwenden",
        "Close": "Schließen",
        "Save": "Speichern",
        "Delete": "Löschen",
        "Add": "Hinzufügen",
        "Remove": "Entfernen",
        "Browse": "Durchsuchen",
        "Refresh": "Aktualisieren",
        "Search": "Suchen",
        "Replace": "Ersetzen",
        "Find": "Suchen",
        "Next": "Weiter",
        "Previous": "Zurück",
        "Clear": "Löschen",
        "Reset": "Zurücksetzen",
        "Default": "Standard",
        # Common dialogs
        "Select": "Auswählen",
        "Choose": "Wählen",
        "Confirm": "Bestätigen",
        "Are you sure?": "Sind Sie sicher?",
        "Select File": "Datei auswählen",
        "Select Directory": "Verzeichnis auswählen",
        "Select Folder": "Ordner auswählen",
        "Save File": "Datei speichern",
        "Open File": "Datei öffnen",
        # Status messages
        "Loading...": "Lädt...",
        "Saving...": "Speichert...",
        "Processing...": "Verarbeitet...",
        "Completed": "Abgeschlossen",
        "Failed": "Fehlgeschlagen",
        "Success": "Erfolg",
        # File dialogs
        "Extract to folder": "In Ordner extrahieren",
        "Select the game directory for {name}": "Spielverzeichnis für {name} auswählen",
        "Save extracted {type} '{name}' as...": "Extrahierten {type} '{name}' speichern als...",
        "An error occurred while fixing corruption:\n{error}": "Beim Reparieren der Korruption ist ein Fehler aufgetreten:\n{error}",
    },
    ToolsetLanguage.ITALIAN: {
        # Main Window
        "Holocron Toolset": "Holocron Toolset",
        "File": "File",
        "Edit": "Modifica",
        "Tools": "Strumenti",
        "Theme": "Tema",
        "Language": "Lingua",
        "Help": "Aiuto",
        "New": "Nuovo",
        "Open": "Apri",
        "Recent Files": "File recenti",
        "Settings": "Impostazioni",
        "Exit": "Esci",
        "Edit Talk Table": "Modifica tabella conversazioni",
        "Edit Journal": "Modifica diario",
        "Module Designer": "Progettista moduli",
        "Indoor Map Builder": "Costruttore mappe interne",
        "KotorDiff": "KotorDiff",
        "TSLPatchData Editor": "Editor TSLPatchData",
        "File Search": "Cerca file",
        "Clone Module": "Clona modulo",
        "About": "Informazioni",
        "Instructions": "Istruzioni",
        "Check For Updates": "Controlla aggiornamenti",
        "Discord": "Discord",
        "Holocron Toolset": "Holocron Toolset",
        "KOTOR Community Portal": "Portale comunitario KOTOR",
        "Deadly Stream": "Deadly Stream",
        # Resource types
        "Core": "Principale",
        "Saves": "Salvataggi",
        "Modules": "Moduli",
        "Override": "Sovrascrivi",
        "Textures": "Texture",
        "Open Selected": "Apri selezionato",
        "Extract Selected": "Estrai selezionato",
        "TPC": "TPC",
        "Decompile": "Decompila",
        "Extract TXI": "Estrai TXI",
        "MDL": "MDL",
        "Extract Textures": "Estrai texture",
        "Open Save Editor": "Apri editor salvataggi",
        "Fix Corruption": "Ripara corruzione",
        "Designer": "Progettista",
        # Dialog/Editor types
        "Dialog": "Dialogo",
        "Creature": "Creatura",
        "Item": "Oggetto",
        "Door": "Porta",
        "Placeable": "Posizionabile",
        "Merchant": "Mercante",
        "Encounter": "Incontro",
        "Trigger": "Trigger",
        "Waypoint": "Punto di passaggio",
        "Sound": "Suono",
        "Script": "Script",
        "TalkTable": "Tabella conversazioni",
        "GFF": "GFF",
        "ERF": "ERF",
        "TXT": "TXT",
        "SSF": "SSF",
        # Tooltips
        "Open the selected save in the Save Editor": "Apri il salvataggio selezionato nell'editor di salvataggi",
        "Fixes all possible save corruption in all saves": "Ripara tutte le possibili corruzioni in tutti i salvataggi",
        "Decompile feature is not available.": "La funzione di decompilazione non è disponibile.",
        # Language selection
        "English": "Inglese",
        "Français": "Francese",
        "Deutsch": "Tedesco",
        "Italiano": "Italiano",
        "Español": "Spagnolo",
        "Polski": "Polacco",
        # Common messages
        "Failed to extract some items.": "Impossibile estrarre alcuni elementi.",
        "Failed to save {count} files!": "Impossibile salvare {count} file(s)!",
        "Extraction successful.": "Estrazione completata.",
        "Successfully saved {count} files to {path}": "Salvati con successo {count} file in {path}",
        "Error Opening Save Editor": "Errore nell'apertura dell'editor di salvataggi",
        "Failed to open save editor:\n{error}": "Impossibile aprire l'editor di salvataggi:\n{error}",
        "Fix Corruption Complete": "Riparazione corruzione completata",
        "Fixed corruption in {count} save(s).": "Corruzione riparata in {count} salvataggio/i.",
        "Failed to fix {count} save(s).": "Impossibile riparare {count} salvataggio/i.",
        "No Corruption Found": "Nessuna corruzione trovata",
        "No corrupted saves were found.": "Nessun salvataggio corrotto trovato.",
        "Corruption Fixed": "Corruzione riparata",
        "Successfully fixed corruption in save:\n{name}": "Corruzione riparata con successo nel salvataggio:\n{name}",
        "Fix Failed": "Riparazione fallita",
        "Failed to fix corruption in save:\n{name}": "Impossibile riparare la corruzione nel salvataggio:\n{name}",
        "This save is corrupted.\nRight click and press <i>'Fix savegame corruption'</i> to fix this.": "Questo salvataggio è corrotto.\nFare clic con il pulsante destro e premere <i>'Fix savegame corruption'</i> per correggerlo.",
        "Native (System Default)": "Nativo (predefinito di sistema)",
        "ERF Editor": "Editor ERF",
        "Debug Reload": "Ricarica debug",
        # Error messages
        "Error": "Errore",
        "Warning": "Avviso",
        "Information": "Informazione",
        "Question": "Domanda",
        # Common buttons/actions
        "OK": "OK",
        "Cancel": "Annulla",
        "Yes": "Sì",
        "No": "No",
        "Apply": "Applica",
        "Close": "Chiudi",
        "Save": "Salva",
        "Delete": "Elimina",
        "Add": "Aggiungi",
        "Remove": "Rimuovi",
        "Browse": "Sfoglia",
        "Refresh": "Aggiorna",
        "Search": "Cerca",
        "Replace": "Sostituisci",
        "Find": "Trova",
        "Next": "Successivo",
        "Previous": "Precedente",
        "Clear": "Cancella",
        "Reset": "Reimposta",
        "Default": "Predefinito",
        # Common dialogs
        "Select": "Seleziona",
        "Choose": "Scegli",
        "Confirm": "Conferma",
        "Are you sure?": "Sei sicuro?",
        "Select File": "Seleziona file",
        "Select Directory": "Seleziona directory",
        "Select Folder": "Seleziona cartella",
        "Save File": "Salva file",
        "Open File": "Apri file",
        # Status messages
        "Loading...": "Caricamento...",
        "Saving...": "Salvataggio...",
        "Processing...": "Elaborazione...",
        "Completed": "Completato",
        "Failed": "Fallito",
        "Success": "Successo",
        # File dialogs
        "Extract to folder": "Estrai in cartella",
        "Select the game directory for {name}": "Seleziona la directory del gioco per {name}",
        "Save extracted {type} '{name}' as...": "Salva {type} estratto '{name}' come...",
        "An error occurred while fixing corruption:\n{error}": "Si è verificato un errore durante la riparazione della corruzione:\n{error}",
    },
    ToolsetLanguage.SPANISH: {
        # Main Window
        "Holocron Toolset": "Holocron Toolset",
        "File": "Archivo",
        "Edit": "Editar",
        "Tools": "Herramientas",
        "Theme": "Tema",
        "Language": "Idioma",
        "Help": "Ayuda",
        "New": "Nuevo",
        "Open": "Abrir",
        "Recent Files": "Archivos recientes",
        "Settings": "Configuración",
        "Exit": "Salir",
        "Edit Talk Table": "Editar tabla de conversación",
        "Edit Journal": "Editar diario",
        "Module Designer": "Diseñador de módulos",
        "Indoor Map Builder": "Constructor de mapas interiores",
        "KotorDiff": "KotorDiff",
        "TSLPatchData Editor": "Editor TSLPatchData",
        "File Search": "Buscar archivos",
        "Clone Module": "Clonar módulo",
        "About": "Acerca de",
        "Instructions": "Instrucciones",
        "Check For Updates": "Buscar actualizaciones",
        "Discord": "Discord",
        "Holocron Toolset": "Holocron Toolset",
        "KOTOR Community Portal": "Portal de la comunidad KOTOR",
        "Deadly Stream": "Deadly Stream",
        # Resource types
        "Core": "Principal",
        "Saves": "Guardados",
        "Modules": "Módulos",
        "Override": "Sobrescribir",
        "Textures": "Texturas",
        "Open Selected": "Abrir seleccionado",
        "Extract Selected": "Extraer seleccionado",
        "TPC": "TPC",
        "Decompile": "Descompilar",
        "Extract TXI": "Extraer TXI",
        "MDL": "MDL",
        "Extract Textures": "Extraer texturas",
        "Open Save Editor": "Abrir editor de guardados",
        "Fix Corruption": "Reparar corrupción",
        "Designer": "Diseñador",
        # Dialog/Editor types
        "Dialog": "Diálogo",
        "Creature": "Criatura",
        "Item": "Objeto",
        "Door": "Puerta",
        "Placeable": "Colocable",
        "Merchant": "Comerciante",
        "Encounter": "Encuentro",
        "Trigger": "Activador",
        "Waypoint": "Punto de referencia",
        "Sound": "Sonido",
        "Script": "Script",
        "TalkTable": "Tabla de conversación",
        "GFF": "GFF",
        "ERF": "ERF",
        "TXT": "TXT",
        "SSF": "SSF",
        # Tooltips
        "Open the selected save in the Save Editor": "Abrir el guardado seleccionado en el editor de guardados",
        "Fixes all possible save corruption in all saves": "Repara toda la corrupción posible en todos los guardados",
        "Decompile feature is not available.": "La función de descompilación no está disponible.",
        # Language selection
        "English": "Inglés",
        "Français": "Francés",
        "Deutsch": "Alemán",
        "Italiano": "Italiano",
        "Español": "Español",
        "Polski": "Polaco",
        # Common messages
        "Failed to extract some items.": "Error al extraer algunos elementos.",
        "Failed to save {count} files!": "Error al guardar {count} archivo(s)!",
        "Extraction successful.": "Extracción exitosa.",
        "Successfully saved {count} files to {path}": "Guardados exitosamente {count} archivo(s) en {path}",
        "Error Opening Save Editor": "Error al abrir el editor de guardados",
        "Failed to open save editor:\n{error}": "Error al abrir el editor de guardados:\n{error}",
        "Fix Corruption Complete": "Reparación de corrupción completada",
        "Fixed corruption in {count} save(s).": "Corrupción reparada en {count} guardado(s).",
        "Failed to fix {count} save(s).": "Error al reparar {count} guardado(s).",
        "No Corruption Found": "No se encontró corrupción",
        "No corrupted saves were found.": "No se encontraron guardados corruptos.",
        "Corruption Fixed": "Corrupción reparada",
        "Successfully fixed corruption in save:\n{name}": "Corrupción reparada exitosamente en guardado:\n{name}",
        "Fix Failed": "Reparación fallida",
        "Failed to fix corruption in save:\n{name}": "Error al reparar la corrupción en el guardado:\n{name}",
        "This save is corrupted.\nRight click and press <i>'Fix savegame corruption'</i> to fix this.": "Este guardado está corrupto.\nHaga clic derecho y presione <i>'Fix savegame corruption'</i> para corregirlo.",
        "Native (System Default)": "Nativo (predeterminado del sistema)",
        "ERF Editor": "Editor ERF",
        "Debug Reload": "Recargar depuración",
        # Error messages
        "Error": "Error",
        "Warning": "Advertencia",
        "Information": "Información",
        "Question": "Pregunta",
        # Common buttons/actions
        "OK": "OK",
        "Cancel": "Cancelar",
        "Yes": "Sí",
        "No": "No",
        "Apply": "Aplicar",
        "Close": "Cerrar",
        "Save": "Guardar",
        "Delete": "Eliminar",
        "Add": "Agregar",
        "Remove": "Quitar",
        "Browse": "Examinar",
        "Refresh": "Actualizar",
        "Search": "Buscar",
        "Replace": "Reemplazar",
        "Find": "Buscar",
        "Next": "Siguiente",
        "Previous": "Anterior",
        "Clear": "Limpiar",
        "Reset": "Restablecer",
        "Default": "Predeterminado",
        # Common dialogs
        "Select": "Seleccionar",
        "Choose": "Elegir",
        "Confirm": "Confirmar",
        "Are you sure?": "¿Está seguro?",
        "Select File": "Seleccionar archivo",
        "Select Directory": "Seleccionar directorio",
        "Select Folder": "Seleccionar carpeta",
        "Save File": "Guardar archivo",
        "Open File": "Abrir archivo",
        # Status messages
        "Loading...": "Cargando...",
        "Saving...": "Guardando...",
        "Processing...": "Procesando...",
        "Completed": "Completado",
        "Failed": "Fallido",
        "Success": "Éxito",
        # File dialogs
        "Extract to folder": "Extraer a carpeta",
        "Select the game directory for {name}": "Seleccionar el directorio del juego para {name}",
        "Save extracted {type} '{name}' as...": "Guardar {type} extraído '{name}' como...",
        "An error occurred while fixing corruption:\n{error}": "Ocurrió un error al reparar la corrupción:\n{error}",
    },
    ToolsetLanguage.POLISH: {
        # Main Window
        "Holocron Toolset": "Holocron Toolset",
        "File": "Plik",
        "Edit": "Edytuj",
        "Tools": "Narzędzia",
        "Theme": "Motyw",
        "Language": "Język",
        "Help": "Pomoc",
        "New": "Nowy",
        "Open": "Otwórz",
        "Recent Files": "Ostatnie pliki",
        "Settings": "Ustawienia",
        "Exit": "Wyjście",
        "Edit Talk Table": "Edytuj tabelę rozmów",
        "Edit Journal": "Edytuj dziennik",
        "Module Designer": "Projektant modułów",
        "Indoor Map Builder": "Budowniczy map wewnętrznych",
        "KotorDiff": "KotorDiff",
        "TSLPatchData Editor": "Edytor TSLPatchData",
        "File Search": "Wyszukiwanie plików",
        "Clone Module": "Klonuj moduł",
        "About": "O programie",
        "Instructions": "Instrukcje",
        "Check For Updates": "Sprawdź aktualizacje",
        "Discord": "Discord",
        "Holocron Toolset": "Holocron Toolset",
        "KOTOR Community Portal": "Portal społeczności KOTOR",
        "Deadly Stream": "Deadly Stream",
        # Resource types
        "Core": "Główne",
        "Saves": "Zapisy",
        "Modules": "Moduły",
        "Override": "Nadpisz",
        "Textures": "Tekstury",
        "Open Selected": "Otwórz zaznaczone",
        "Extract Selected": "Wyodrębnij zaznaczone",
        "TPC": "TPC",
        "Decompile": "Dekompiluj",
        "Extract TXI": "Wyodrębnij TXI",
        "MDL": "MDL",
        "Extract Textures": "Wyodrębnij tekstury",
        "Open Save Editor": "Otwórz edytor zapisów",
        "Fix Corruption": "Napraw uszkodzenia",
        "Designer": "Projektant",
        # Dialog/Editor types
        "Dialog": "Dialog",
        "Creature": "Stworzenie",
        "Item": "Przedmiot",
        "Door": "Drzwi",
        "Placeable": "Umieszczalny",
        "Merchant": "Kupiec",
        "Encounter": "Spotkanie",
        "Trigger": "Wyzwalacz",
        "Waypoint": "Punkt nawigacyjny",
        "Sound": "Dźwięk",
        "Script": "Skrypt",
        "TalkTable": "Tabela rozmów",
        "GFF": "GFF",
        "ERF": "ERF",
        "TXT": "TXT",
        "SSF": "SSF",
        # Tooltips
        "Open the selected save in the Save Editor": "Otwórz zaznaczony zapis w edytorze zapisów",
        "Fixes all possible save corruption in all saves": "Naprawia wszystkie możliwe uszkodzenia zapisów",
        "Decompile feature is not available.": "Funkcja dekompilacji nie jest dostępna.",
        # Language selection
        "English": "Angielski",
        "Français": "Francuski",
        "Deutsch": "Niemiecki",
        "Italiano": "Włoski",
        "Español": "Hiszpański",
        "Polski": "Polski",
        # Common messages
        "Failed to extract some items.": "Nie udało się wyodrębnić niektórych elementów.",
        "Failed to save {count} files!": "Nie udało się zapisać {count} pliku/ów!",
        "Extraction successful.": "Wyodrębnianie zakończone powodzeniem.",
        "Successfully saved {count} files to {path}": "Pomyślnie zapisano {count} pliku/ów w {path}",
        "Error Opening Save Editor": "Błąd podczas otwierania edytora zapisów",
        "Failed to open save editor:\n{error}": "Nie udało się otworzyć edytora zapisów:\n{error}",
        "Fix Corruption Complete": "Naprawa uszkodzeń zakończona",
        "Fixed corruption in {count} save(s).": "Naprawiono uszkodzenia w {count} zapisie/ach.",
        "Failed to fix {count} save(s).": "Nie udało się naprawić {count} zapisu/ów.",
        "No Corruption Found": "Nie znaleziono uszkodzeń",
        "No corrupted saves were found.": "Nie znaleziono uszkodzonych zapisów.",
        "Corruption Fixed": "Uszkodzenia naprawione",
        "Successfully fixed corruption in save:\n{name}": "Pomyślnie naprawiono uszkodzenia w zapisie:\n{name}",
        "Fix Failed": "Naprawa nie powiodła się",
        "Failed to fix corruption in save:\n{name}": "Nie udało się naprawić uszkodzeń w zapisie:\n{name}",
        "This save is corrupted.\nRight click and press <i>'Fix savegame corruption'</i> to fix this.": "Ten zapis jest uszkodzony.\nKliknij prawym przyciskiem i naciśnij <i>'Fix savegame corruption'</i>, aby to naprawić.",
        "Native (System Default)": "Natywny (domyślny system)",
        "ERF Editor": "Edytor ERF",
        "Debug Reload": "Przeładuj debug",
        # Error messages
        "Error": "Błąd",
        "Warning": "Ostrzeżenie",
        "Information": "Informacja",
        "Question": "Pytanie",
        # Common buttons/actions
        "OK": "OK",
        "Cancel": "Anuluj",
        "Yes": "Tak",
        "No": "Nie",
        "Apply": "Zastosuj",
        "Close": "Zamknij",
        "Save": "Zapisz",
        "Delete": "Usuń",
        "Add": "Dodaj",
        "Remove": "Usuń",
        "Browse": "Przeglądaj",
        "Refresh": "Odśwież",
        "Search": "Szukaj",
        "Replace": "Zastąp",
        "Find": "Znajdź",
        "Next": "Następny",
        "Previous": "Poprzedni",
        "Clear": "Wyczyść",
        "Reset": "Resetuj",
        "Default": "Domyślny",
        # Common dialogs
        "Select": "Wybierz",
        "Choose": "Wybierz",
        "Confirm": "Potwierdź",
        "Are you sure?": "Czy jesteś pewien?",
        "Select File": "Wybierz plik",
        "Select Directory": "Wybierz katalog",
        "Select Folder": "Wybierz folder",
        "Save File": "Zapisz plik",
        "Open File": "Otwórz plik",
        # Status messages
        "Loading...": "Ładowanie...",
        "Saving...": "Zapisywanie...",
        "Processing...": "Przetwarzanie...",
        "Completed": "Zakończono",
        "Failed": "Niepowodzenie",
        "Success": "Sukces",
        # File dialogs
        "Extract to folder": "Wyodrębnij do folderu",
        "Select the game directory for {name}": "Wybierz katalog gry dla {name}",
        "Save extracted {type} '{name}' as...": "Zapisz wyodrębniony {type} '{name}' jako...",
        "An error occurred while fixing corruption:\n{error}": "Wystąpił błąd podczas naprawiania uszkodzeń:\n{error}",
    },
}


class Translator:
    """Translation manager for the Holocron Toolset."""

    def __init__(self, language: ToolsetLanguage = ToolsetLanguage.ENGLISH):
        """Initialize the translator with a language."""
        self._language: ToolsetLanguage = language

    @property
    def language(self) -> ToolsetLanguage:
        """Get the current language."""
        return self._language

    @language.setter
    def language(self, value: ToolsetLanguage) -> None:
        """Set the current language."""
        self._language = value

    def translate(self, text: str, fallback: str | None = None) -> str:
        """Translate a string to the current language.

        Args:
        ----
            text: The English text to translate
            fallback: Optional fallback text if translation not found

        Returns:
        -------
            The translated string, or the original text if translation not found
        """
        if self._language == ToolsetLanguage.ENGLISH:
            return text

        translations = _TRANSLATIONS.get(self._language, {})
        translated = translations.get(text, None)

        if translated is not None:
            return translated

        # Try fallback if provided
        if fallback:
            translated = translations.get(fallback, None)
            if translated is not None:
                return translated

        # Return original if no translation found
        return text

    def tr(self, text: str, fallback: str | None = None) -> str:
        """Alias for translate() for convenience."""
        return self.translate(text, fallback)


# Global translator instance
_global_translator: Translator = Translator(ToolsetLanguage.ENGLISH)


def set_language(language: ToolsetLanguage) -> None:
    """Set the global language for translations."""
    _global_translator.language = language


def get_language() -> ToolsetLanguage:
    """Get the current global language."""
    return _global_translator.language


def translate(text: str, fallback: str | None = None) -> str:
    """Translate text using the global translator.

    Args:
    ----
        text: The English text to translate
        fallback: Optional fallback text if translation not found

    Returns:
    -------
        The translated string
    """
    return _global_translator.translate(text, fallback)


def tr(text: str, fallback: str | None = None) -> str:
    """Alias for translate() for convenience."""
    return translate(text, fallback)


def trf(text: str, **kwargs) -> str:
    """Translate and format a string with placeholders.
    
    Args:
    ----
        text: The English text template with {placeholders}
        **kwargs: Values to format into the placeholders
    
    Returns:
    -------
        The translated and formatted string
        
    Example:
    -------
        trf("Failed to save {count} files!", count=5)
    """
    translated = translate(text, None)
    try:
        return translated.format(**kwargs)
    except KeyError:
        # If formatting fails, return translated text without formatting
        return translated

