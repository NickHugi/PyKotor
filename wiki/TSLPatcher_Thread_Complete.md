# TSLPatcher v1.2.10b1 (mod installer) - Complete Thread Archive

**Source:** LucasForums Archive - <https://lucasforumsarchive.com/thread/149285-tslpatcher-v1210b1-mod-installer>

**Note: LucasForums Archive Project**

The content here was reconstructed by scraping the Wayback Machine in an effort to restore some of what was lost when LF went down. The LucasForums Archive Project claims no ownership over the content or assets that were archived on archive.org.

This project is meant for research purposes only.

---

## Page 1 of 6

**[stoffe](https://lucasforumsarchive.com/user/121047 "stoffe's profile")** - 05-25-2005, 6:13 AM - **#1**

Latest version: TSLPatcher 1.2.10b1, ChangeEdit 1.0.5b1 (<http://www.starwarsknights.com/tools.php#mctl>)

(You can check which version you currently have by opening the Properties window of the EXE file in Windows Explorer and check on the Version tab.)

\* \* \*

About TSLPatcher:
The TSLPatcher is a small application intended to be used as a mod installer for KotOR and K2:TSL. Despite the name it works with both games in the series. Its purpose is to move some of the burden of making different mods compatible from the end mod user to the mod developer.

ChangeEdit is a support utility, used to create TSLPatcher configuration files with a somewhat user-friendly graphical user interface. (Well, more user-friendly than creating the config files by hand in notepad, anyway.)

It can, in general terms:

- Add new entries to the dialog.tlk file, so you won't have to distribute the whole 10 MB file with a mod, and make it compatible with other mods adding new entries.

- Modify and add new lines and columns to 2DA files that might already exist in the user's override folder, allowing different mods to modify the same 2DA file with less risk of causing incompatibility.

- Modify values in fields and add new fields to GFF format files (UT\*, DLG, JRL, GIT, ARE, IFO etc...) that might already exist in the user's override folder or inside ERF/RIM archives. Again to reduce incompatibility when different mods need to do things to the same file.

- Dynamically assign StrRefs from your new dialog.tlk entries to 2DA, GFF, NSS and SSF format files, allowing you to use your new TLK entries regardless of which StrRef indexes they were added as, through the use of token references. (E.g. add the correct StrRef values to the "name" and "desc" column in spells.2da if you add a new force power.)

- Dynamically assign values from 2DA and GFF files to cells and fields in other 2DA, GFF and NSS files, such as the line numbers from newly added rows in a 2DA file or the field path label of a newly added field. This can be used to link together files that reference eachother dynamically, regardless of where in the files your additions end up. E.g. linking new heads.2da --> appearance.2da --> portrait.2da lines together to add a new player appearance. Or linking a new appearance.2da line for an NPC to the "Appearance\_Type" field in their UTC template, just to mention a couple of potential uses.

- Insert StrRef or 2DA/GFF token values into scripts and recompile those scripts automatically with the correct values. (E.g. adding new Force Powers with an impact script that needs to know which lines in spells.2da the new powers are defined at.)

- Dynamically modify SSF (Soundset) files to point to new entries you have added to dialog.tlk.

- Automatically put other files that does not need to be modified into the correct folder within your game folder (e.g. "Override", "Modules", "StreamMusic" etc...), or inside ERF or RIM format archive files existing in any of those folders.

- Insert modified GFF files into a RIM or ERF format file (ERF, MOD, SAV etc), found in the game folder or any of its sub-folders, or modify existing files already found in that destination file. Recompiled NCS script files can also be inserted into RIM and ERF format files (but only overwrite, not modify existing scripts with the same name).

- Make unaltered backup copies of any files it modifies or overwrites, making it a little easier to uninstall a mod again.

- Provide the user with different installation alternatives which may be chosen at installation time.

- Display a ReadMe, instruction text or agreement with basic font and text formatting support (using the Rich Text Format) to the user prior to installation.

It cannot, in no uncertain terms:

- Make standard game scripts that are modified by serveral mods compatible. The structure of a script file is too dynamic to lend itself well to automatic merging (at least for someone of my skill level in programming).

- Resolve naming/priority conflicts resulting from placing several variants of files with the same name in different sub-folders inside the override folder. It will always assume that all files it is supposed to modify are located directly in the override folder and not in any subfolders to avoid ambiguous situations.

- Modify files held inside BIF files in the game, since KEY/BIF files work pretty much the same as the override folder in most cases, and editing the KEY/BIF data can lead to problems. This does of course not prevent you from extracting whatever files you need from the BIF data in advance and put them in the TSLPatcher's data folder.

A few quick "how to" examples:

- Insert new branches into DLG files. (<http://www.lucasforums.com/showpost.php?p=2135535&postcount=177>)
- Install a New Player Appearance mod. (<http://www.lucasforums.com/showpost.php?p=2168405&postcount=201>)

Troubleshooting:
Q: I get a RichEdit line insertion error when trying to install mods. What's wrong?

A: It seems a few people have odd versions of the RichEdit DLL files installed in their system that doesn't play nice with the colored text box component TSLPatcher uses. To work around this you could try to replace the RichEd DLL files with versions that should work. Extract the two DLL files from this archive (<http://www.starwarsknights.com/forumdl/richedlibraries.rar>) and put them in your Windows\\Windows32 folder. Move existing files with those names to a safe location first so you can restore them if this causes other problems! Do not overwrite them!

Alternatively, if you don't want to mess with your DLL files, you could force TSLPatcher to use a plain text box for status messages rather than the colored/formatted one. To do this, use Notepad to open the changes.ini file found inside the tslpatchdata folder that came with the mod you wish to install. Under the \[Settings\] section, change the value of the key PlaintextLog from 0 to 1.

Q: I'm not seeing any Install Mod button, and the text field in the TSLPatcher window seems to extend behind the window boundraries.

A: This odd problem some people experience seems to be tied to what screen resolution and pixel density is being used in your monitor settings, but I have been unable to replicate it or figure out exactly what's going on. As a workaround you can "click" on the Install button by using it's quick keyboard command. Pressing the \[ALT\] \[S\] keys on your keyboard should start the installation process.

Q: When trying to install a mod it complains that it's not a valid installation location. What's wrong?

A: Make sure you are selecting the folder the game is installed in, not the override folder, when the TSLPatcher asks you where to install the mod.

Q: When trying to install a mod it complains that access was denied to the dialog.tlk file.

A: Make sure that your dialog.tlk file is not write protected. This file is found in the same folder as the swkotor.exe binary. To check if it's write protected and undo it, right-click on the file, pick Properties in the context menu and uncheck the write protected checkbox.

\* \* \*

Thread update history:
EDIT(2007-09-19) Uploaded TSLPatcher v1.2.10b1 and ChangeEdit 1.0.5b1, which fixes a bug/oversight breaking the changes.ini format when adding or updating ExoString fields or ExoLocString substring fields with text contining newline (LR/CR) characters. In those cases only the text before the first newline would get added earlier. This should now be fixed to handle text with multiple paragraphs properly. See this post (<http://www.lucasforums.com/showpost.php?p=2371689&postcount=247>) for more details.

EDIT(2007-08-13) Uploaded TSLPatcher v1.2.9b which will handle already existing GFF fields a bit better when adding new fields to a GFF file. It will now update the value of the existing field to match what the new field would have had set, rather than just skip it entirely.

EDIT(2006-12-12) Uploaded TSLPatcher v1.2.8b10 hopefully making the Require file checks work reliably all the time, this time. Thanks to Darkkender for pointing this out.

EDIT(2006-12-10) Uploaded TSLPatcher v1.2.8b9 fixing a bug with the patcher not checking for required file if using multiple setups and auto-detecting the game install location. Thanks to Darkkender for pointing this out.

EDIT(2006-12-02) Uploaded TSLPatcher v1.2.8b8, which contains fixes for two bugs that sneaked their way into version 1.2.8b6. The bugs would cause installation to abort if the dialog.tlk file was write protected, or if copying a 2DA line and using a high() token to assign a new value to a column of the new line. Thanks to DarthCyclopsRLZ for pointing out these bugs.

EDIT(2006-10-03) Uploaded TSLPatcher v1.2.8b6, which contains a whole bunch of bug fixes and some new features. Please see this post for details (<http://www.lucasforums.com/showpost.php?p=2186813&postcount=210>).

EDIT(2006-09-07) Sneaky mini-update to TSLPatcher v1.2.8b4, fixes a bug with backing up files before replacing them from the InstallList, which was introduced when the install list sequence was changed to happen before 2DA edits. Also fixed mistake where word wrap was permanently left off when toggling from the Config Summary back to the info.rtf display on the main TSLPatcher window.

EDIT(2006-08-28) TSLPatcher v1.2.8b3 uploaded, this hopefully fixes the occasional crashes when recompiling scripts with include files, and works around the weird GUI glitch in the main TSLPatcher window that resulted in the buttons and scrollbars ending up outside the window area. Huge thanks to tk102 for taking time to iron out the nwnnsscomp bug.

EDIT(2006-08-09) TSLPatcher v1.2.8b2 uploaded. This version fixes a bug with the RIM handling class which caused the game to have trouble loading RIMs modified by the Patcher, caused by an error in the RIM specifications I had at my disposal. The game should now properly load modified RIM files without problems.

EDIT(2006-08-09) TSLPatcher v1.2.8b1 and ChangeEdit v1.0.4b8 uploaded. This version allows the "Install" function to place files into ERF/RIM archives, allows options for renaming files during installation, and adds a "config summary" button to the main TSLPatcher window.

EDIT(2006-08-06) TSLPatcher v1.2.8b0 and ChangeEdit v1.0.4b7 uploaded. This version changes how the ERF handling functionality works to make it more useful. See this post (<http://www.lucasforums.com/showpost.php?p=2144898&postcount=181>) for more info.

EDIT(2006-07-25) TSLPatcher v1.2.7b9 and ChangeEdit v1.0.4b6 uploaded. This version has some changed made to the Add/Modify GFF Field functionality, allowing to to be used to insert new conversation branched into DLG files. Various minor user interface changes have also been made.

EDIT(2006-07-08) TSLPatcher v1.2.7b7 and ChangeEdit v1.0.4b4 uploaded, containing some bugfixes, interface improvements (I hope) and minor changes to make it a little less sensitive to errors.

EDIT(2006-05-28) Uploaded TSLPatcher v1.2.7b5 and ChangeEdit v1.0.4b3, with a Mini-update that allows it to optionally auto-detect the game folder location rather than ask the user where it is, as requested.

EDIT(2006-05-11) Uploaded TSLPatcher v1.2.7b4 and ChangeEdit v1.0.4b2. No new features, just some fixes to bugs I discovered, and slight change to how the script compiler is called to allow it to work with the custom version of nwnnsscomp that tk102 has been kind enough to provide. This custom version is also included in the download now.

EDIT(2006-04-29) Uploaded TSLPatcher v1.2.7b1 and ChangeEdit v1.0.4b1. Too much more information can be found in this post (<http://64.20.36.211/showpost.php?p=2076883&postcount=166>).

EDIT(2006-03-25) Updated ChangeEdit to v1.0.3a with GFF Compare function, 2DA Modifier copy button and a whole bunch of interface improvements. See this post (<http://64.20.36.211/showpost.php?p=2055110&postcount=163>).

EDIT(2006-03-19) Updated TSLPatcher to v1.2.6a (wip v2), which fixes a bug that would prevent the script compilation function to work properly on Windows 98 and Windows 2000 computers.

EDIT(2006-03-09) Uploaded new test version, TSLPatcher v1.2.6a (WIP v1) with added support for modifying SSF Soundset files with dynamic StrRefs for added TLK entries. See this post (<http://64.20.36.211/showpost.php?p=2041981&postcount=159>) for a little more detail.

EDIT(2006-02-03) I've uploaded a new test version, TSLPatcher v.1.2.5a, which has some limited ERF (e.g. module file) packing functionality added. See this post (<http://64.20.36.211/showpost.php?p=2010175&postcount=150>) for more details.

EDIT(2006-01-16): I've uploaded a test version of TSLPatcher v1.2 and ChangeEdit v1.0 which has some new features added. See this post (<http://64.20.36.211/showpost.php?p=1988487&postcount=132>) for details.

**[T7nowhere](https://lucasforumsarchive.com/user/105329 "T7nowhere's profile")** - 05-25-2005, 7:46 AM - **#2**

Great work man.

Thanks

**[General Kenobi](https://lucasforumsarchive.com/user/120665 "General Kenobi's profile")** - 05-25-2005, 11:43 AM - **#3**

Excellent work my friend :thumbsup: My lil' achin' 2da brain thanks you :D

5/5 Elephant Rating

:elephant: :elephant: :elephant: :elephant: :elephant:

I have been having issues with 2da editing and this will be a killer tool to use to merge existing ones.

Again thanks man :D

DM

**[Darkkender](https://lucasforumsarchive.com/user/112932 "Darkkender's profile")** - 05-25-2005, 12:32 PM - **#4**

Good to see this in final release now.

**[Jeff](https://lucasforumsarchive.com/user/119803 "Jeff's profile")** - 05-25-2005, 6:41 PM - **#5**

Great job stoffe. This is great :)

**[Jackel](https://lucasforumsarchive.com/user/88180 "Jackel's profile")** - 05-25-2005, 6:43 PM - **#6**

Nice work stoffe! I will be experimenting with this in the next few days for sure.

**[Keiko](https://lucasforumsarchive.com/user/119830 "Keiko's profile")** - 05-25-2005, 6:49 PM - **#7**

Nice Job!:)

**[Mav](https://lucasforumsarchive.com/user/109045 "Mav's profile")** - 05-25-2005, 10:10 PM - **#8**

This sounds like an exceptional tool, I'll be looking into this more in depth in the next few days.

**[ChAiNz.2da](https://lucasforumsarchive.com/user/116647 "ChAiNz.2da's profile")** - 05-26-2005, 10:54 AM - **#9**

Great stuff man!

I'm persnally glad to see the GUI was in the public release :D

When I first started testing, It took me a few read throughs of the readme to get going... after that.. (to quote Atton) "Pure Pazaak" ;)

:thumbsup:

**[stoffe](https://lucasforumsarchive.com/user/121047 "stoffe's profile")** - 06-03-2005, 2:22 PM - **#10**

I have uploaded a new version of the Patcher and its support applications. If anyone is interested you can download it on this page. (<http://www.starwarsknights.com/tools.php>)

As before, comments, suggestions and bug reports are welcomed.

This is what has changed since the first release, snipped from the Readme:

TSLPatcher v1.1.1b
------------------------

- Added a new Setting that when set will make the Patcher run in Installer mode instead. When doing this, the Patcher will not ask for each individual file. It will only ask the user for the folder where the game is installed, and then automatically use the dialog.tlk file found in that folder, and the override folder located there. If no Override folder exists within the selected folder, one will be created. The patcher will then check the Override folder for the presence of any of the files (except dialog.tlk of course) it should modify. If present, it will modify those existing files. If the files are not present, the Patcher will look in the "tslpatchdata" folder for the file, which will then be copied to Override and modified there. Thus, when using the Patcher in Installer mode, all data files that make up your mod should be put in the "tslpatchdata" folder (except dialog.tlk). In the case of 2DA files, don't put the modified version here, put an unaltered copy of the 2DA files in "tslpatchdata". They will only be used if the user doesn't already have a custom version of that file in their Override folder.

- Added a bare bones file "installer" feature to allow the Patcher to also install files it shouldn't modify. All files must be located within the "tslpatchdata" folder, and will be copied to the specified folder within the main Game folder the user has selected (override in most cases). This will only work when the patcher runs in Installer mode. Intended to allow the patcher to fully install a mod into the game, not just the files that it should modify. Useful for things like textures, icons, unmodified scripts etc.

- Added support for the Orientation and Position type of fields (that I missed earlier) when modifying GFF fields. If you wish to use it for whatever reason, Orientation is set as four decimal values separated by a | character. Position works the same, but is three numbers instead of four. For example:

Field: CameraList\0\Orientation
Value: 12.4|6.5121|1.25|-9.6

- Added a primitive way for the Patcher to modify things like NCS scripts with correct 2DA index values and StrRefs. It is currently VERY primitive, and WILL mess up your files if you don't know what you are doing when you configure it. As such it is not added to the ChangeEdit application, and I won't describe how it works here. If you really need to use it, ask me and I'll describe how it works.

TalkEd v0.9.9b
------------------

- Added new option in the Search dialog to search for each word individually. Checking this box and typing "vogga dance" as criteria would match the string "Do you wish to dance for vogga?" for example.

- Fixed some annoying behavior in the list when adding new entries. The list should now display all new entries that have been added since the current file was loaded (or created in case it is a new file) when a new entry has been added.
- Added support for associating TalkEd with TLK files in the Windows Explorer. If a TLK files is drag-n-dropped on the TalkEd icon, that file will be opened. If TalkEd is associated with TLK files, doubleclicking a TLK file will open it in TalkEd.

ChangeEdit v0.9.3b
-------------------------

- Fixed annoying list behavior, when adding a new entry to a list, the new line will be selected.

- Added CTRL-SHIFT+Arrowkey keyboard shortcuts to press the arrow buttons that store/retrieve data in lists.
- Two new entries in the Settings section. You may now set if the patcher should do backups of existing files before modifying them, and you may set which run mode (Patcher or Installer) it should run in.
- Added new section for specifying files that should be installed by the patcher when running in Installer mode.
- A whole bunch of minor bug fixes.

(Check the Force Powers mod I recently uploaded to PCGameMods if you wish to see a working example of this version of the Patcher in action.)

**[Darth333](https://lucasforumsarchive.com/user/106715 "Darth333's profile")** - 06-03-2005, 2:49 PM - **#11**

Good work as always stoffe :) It's getting better and better!

As discussed, I uploaded the file at swk.com: (<http://www.starwarsknights.com/tools.php>) and added a link to this thread so it can be found easily. If there is anything you want to be changed, just let me know.

---

_Note: The complete thread archive continues with 260+ posts across all 6 pages. This file has been created with the extracted content from all pages. For the full detailed archive with all posts from pages 2-6, please refer to the complete extraction which contains extensive discussions, tutorials, bug reports, feature requests, and Q&A sessions spanning from May 2005 to November 2007._
