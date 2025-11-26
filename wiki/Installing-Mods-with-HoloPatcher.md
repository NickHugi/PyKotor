# Using HoloPatcher: Installation and Reversion

_This page explains how to install mods with HoloPatcher. If you are a mod developer, you may be looking for [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.)_

HoloPatcher aims to offer a user experience identical to TSLPatcher. Follow these steps for a smooth mod installation:

**Select Mod Folder:** Direct HoloPatcher to the mod folder containing the 'tslpatchdata' folder.
**Select Game Directory:** Point HoloPatcher to your KotOR game directory. These paths are often pre-populated in dropdown menus for convenience.
**Choose Installation Option:** If the mod provides multiple installation options (indicated by a namespaces.ini file), select your preferred option from the first dropdown menu.
After configuring, click 'install' to initiate the patching process.

## Reverting Mod Installations

To undo the modifications made by a recent mod installation:

**Navigate to Tools -> Uninstall Mod/Restore Backup from the top menu.** This action restores your game files to their state just before the latest mod installation, effectively undoing all recent changes.
Important: Avoid Multiple Installations
Do not reinstall the same mod using the same option without first reverting previous changes. This is crucial for several reasons:

**Partial Installations:** If an installation is interrupted (for example, if the app is closed prematurely) and then restarted, the mod is reapplied over partially modified files. This can result in duplication within critical game files, such as appearance.2da, leading to potential game-breaking issues.

**Correcting Mistakes:** If you inadvertently install a mod multiple times without reverting, the game files may contain redundant modifications. However, HoloPatcher keeps backups for each installation. To correct this, you must use the Uninstall Mod/Restore Backup feature twice:

The first execution removes the modifications from the most recent (second) installation, reverting files to their state after the first (interrupted) installation.
The second execution then removes the remaining modifications, fully reverting your game files to their original state before any installation attempts.

## Installing Mods on iOS Devices

For iOS installations, it's critical to ensure that all KotOR file names are in lowercase. If file names retain uppercase characters, the game will crash immediately after tapping the 'play' button on the main menu.

To prevent this issue, HoloPatcher includes a specific utility designed to address iOS's case sensitivity:

- **Navigate to Tools -> Fix iOS Case Sensitivity within HoloPatcher.**
- **Direct the tool to your KotOR directory or install folder.** If you're applying mods specifically for the mobile version of The Sith Lords Restored Content Mod (TSLRCM), point the tool to the 'mtslrcm' directory.
This step is essential for a successful mod installation on iOS devices, ensuring stability and preventing crashes due to case sensitivity conflicts.
