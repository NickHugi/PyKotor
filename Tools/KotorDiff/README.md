## KotorDiff

- ![Screenshot 1](https://deadlystream.com/downloads/screens/monthly_2023_09/Code_B7XMgAobTn.thumb.png.031c5f751b0fc2255f2de5300d42af7f.png)
- ![Screenshot 2](https://deadlystream.com/downloads/screens/monthly_2023_09/Code_sUtiSdkEsB.thumb.png.bff397075b009ba2140696ed3c38deed.png)

## About This File

### **A simple CLI to easily compare KOTOR file formats.**

This is a very simple CLI to PyKotor. If you find TSLPatcher isn't patching the resulting files in the way you want, you can use this tool to compare your manual changes to the resulting TSLPatcher result. You can also use it to compare entire installations, directories, or single files.

### **Why KotorDiff?**

It is (or should be) common knowledge that Kotor Tool is not safe to use for anything besides extraction. But have you ever wondered *why* that is?

Let's take a look at a **.utc** file extracted directly from the BIFs (the OG vanilla **p_bastilla.utc**). Extract it with **KTool** and name it **p_bastilla_ktool.utc**. Now open the same file in ktool's UTC character editor, change a single field (literally anything, hp, strength, whatever you fancy), and save it as **p_bastilla_ktool_edited.utc**.

KotorDiff's output:

```diff
Using --path1='C:\Users\nodoxxxpls\Downloads\p_bastilla_ktool_edited.utc'
Using --path2='C:\Users\nodoxxxpls\Downloads\p_bastilla_ktool.utc'
Using --ignore-rims=False
Using --ignore-tlk=False
Using --ignore-lips=False
Using --compare-hashes=True
Using --use-profiler=False

GFFStruct: number of fields have changed at 'p_bastilla_ktool_edited.utc': '72' --> '69'
Field 'Int16' is different at 'p_bastilla_ktool_edited.utc\HitPoints':
--- (old)HitPoints
+++ (new)HitPoints
@@ -1 +1 @@
-18
+24
Field 'LocalizedString' is different at 'p_bastilla_ktool_edited.utc\FirstName':
--- (old)FirstName
+++ (new)FirstName
@@ -1 +1 @@
-Bastila
+31360
Field 'Int16' is different at 'p_bastilla_ktool_edited.utc\CurrentHitPoints':
--- (old)CurrentHitPoints
+++ (new)CurrentHitPoints
@@ -1 +1 @@
-20
+24
Field 'UInt16' is different at 'p_bastilla_ktool_edited.utc\FeatList\0\Feat':
--- (old)Feat
+++ (new)Feat
@@ -1 +1 @@
-3
+94
Field 'UInt16' is different at 'p_bastilla_ktool_edited.utc\FeatList\2\Feat':
--- (old)Feat
+++ (new)Feat
@@ -1 +1 @@
-39
+98
Field 'UInt16' is different at 'p_bastilla_ktool_edited.utc\FeatList\3\Feat':
--- (old)Feat
+++ (new)Feat
@@ -1 +1 @@
-43
+55
Field 'UInt16' is different at 'p_bastilla_ktool_edited.utc\FeatList\4\Feat':
--- (old)Feat
+++ (new)Feat
@@ -1 +1 @@
-44
+107
Field 'UInt16' is different at 'p_bastilla_ktool_edited.utc\FeatList\5\Feat':
--- (old)Feat
+++ (new)Feat
@@ -1 +1 @@
-55
+3
Field 'UInt16' is different at 'p_bastilla_ktool_edited.utc\FeatList\6\Feat':
--- (old)Feat
+++ (new)Feat
@@ -1 +1 @@
-94
+39
Field 'UInt16' is different at 'p_bastilla_ktool_edited.utc\FeatList\7\Feat':
--- (old)Feat
+++ (new)Feat
@@ -1 +1 @@
-98
+43
Field 'UInt16' is different at 'p_bastilla_ktool_edited.utc\FeatList\8\Feat':
--- (old)Feat
+++ (new)Feat
@@ -1 +1 @@
-107
+44
Field 'LocalizedString' is different at 'p_bastilla_ktool_edited.utc\Description':
--- (old)Description
+++ (new)Description
@@ -0,0 +1 @@
+-1
Field 'String' is different at 'p_bastilla_ktool_edited.utc\Subrace':
--- (old)Subrace
+++ (new)Subrace
@@ -1 +0,0 @@
-0
^ 'p_bastilla_ktool_edited.utc': GFF is different ^
---------------------------------------------------
'p_bastilla_ktool_edited.utc'  DOES NOT MATCH  'p_bastilla_ktool.utc'
```

Sheesh! I bet you can't even guess which field I modified! Again, I changed a singular field! What is all this nonsense that KTool did to my character sheet?

Moral: Don't use KTool to modify files. It seems to have the incorrect field types defined internally and doesn't respect the original file when saving a new one.

But KotorDiff saved the day here and outputted exactly what happened on save.

### **How to use:**

Simply run the executable. It'll ask you for 3 paths:

- **PATH1**: *Path to the first K1/TSL install, file, or directory to diff.*
- **PATH2**: *Path to the second K1/TSL install, file, or directory to diff.*
- **OUTPUT_LOG**: *File name/path of the desired output logfile (defaults to `log_install_differ.log` in the current directory).*

If you point **PATH1** and **PATH2** to two KOTOR installs, it will ONLY compare the **Override** folder, the **Modules** folder, the **Lips** folder, the **rims** folder (if exists), the **StreamWaves/StreamVoices** folder, and the **dialog.tlk** file. This was a design choice to improve how long the differ takes to finish. This includes any subfolders within the aforementioned folder names.

### **Supported filetypes/formats:**

- TalkTable files (TLK)
- Any GFF file (DLG, UTC, GUI, UTP, UTD, GIT, IFO, etc.)
- Any capsule (ERF, MOD, RIM, SAV, etc.)

**Not supported:** NCS, NSS, ITP

*Any file format that's not supported will have its SHA256 hash compared instead.*

### **CLI Support:**

This is a very flexible tool. You can send it command line arguments if you would like to use it in a 3rd party tool. Run `kotordiff.exe --help` to get a full syntax. If there's an error, the exit code will be 3 (if the error is known by my code) or 1 (some system error loading the tool). If the two paths match, the exit code will be 0. If the two paths don't match, the exit code will be 2. You can utilize these error codes to use KotorDiff in a customized 3rd party script or as an add-on to WinMerge/WinDirStat; the possibilities are endless.

### **FAQ:**

**Q: I am struggling to read the diff output, why is it saying +/-/@38924 and what does it mean?**

A: GIT Diff is a standardized output format that has been widely adopted and used since probably the 80s/90s. [This StackOverflow answer](https://stackoverflow.com/a/2530012/4414190) is by far the best explanation I've seen, but honestly, ask ChatGPT to explain it further if needed, or send me a PM if something doesn't make sense!

**Q: Couldn't I just open my two files with Holocron Toolset/ERFEdit/K-GFF etc?**

A: You could, but for me, it became tedious to manually compare them side by side, expanding every node, etc. Leave alone completely multiple files. This tool allows you to simply input two paths and have the full differences outputted and logged.

A main benefit is it'll show you the exact GFF paths that differ. Output such as `Missing struct: "EntryList\5\RepliesList\3" {contents of the struct}` has been very useful.

**Q: Why is my antivirus flagging this?**

A: This is a false positive and there's nothing I can do. Python source scripts are compiled to executables using [PyInstaller](https://github.com/pyinstaller/pyinstaller), but unfortunately, some antiviruses have been known to flag anything compiled with PyInstaller this way. The problem is similar to why your browser may warn you about downloading any files with the .EXE extension.

This whole tool is open source, feel free to run directly from the source script: [https://github.com/th3w1zard1/PyKotor/blob/master/Tools/KotorDiff/src/\_\_main\_\_.py](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/KotorDiff/src/__main__.py)

There's a well-written article explaining why the false positives happen on their issue template: [https://github.com/pyinstaller/pyinstaller/blob/develop/.github/ISSUE_TEMPLATE/antivirus.md](https://github.com/pyinstaller/pyinstaller/blob/develop/.github/ISSUE_TEMPLATE/antivirus.md)

**TLDR:** PyInstaller is an amazing tool, but antiviruses may flag it. This is not the fault of PyInstaller or my tool, but rather the fault of how some scummy users have chosen to use PyInstaller in the past. Please report any false positives you encounter to your antivirus's website, as reports not only improve the accuracy of everybody's AV experience overall but also indirectly support the [PyInstaller project](https://github.com/pyinstaller/pyinstaller).

### **Source code:**

[https://github.com/th3w1zard1/PyKotor/blob/master/Tools/KotorDiff](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/KotorDiff/)

### **Credit:**

**@Cortisol** for creating the PyKotor library (i.e., 90% of the code for this tool)
