## Override Resources
Override resources refer to the resources stored in the game’s override folder. These can be found in the “/override/” folder of your game directory. Override files can be accessed by any module in the game and take priority over core and module resources.

Warning: Because override resources take the highest priority and are accessible by any module, it makes conflicts likely to occur. For example if I have a creature file named “n_rodian01” stored in both the Citadel Station Cantina and Nar Shaddaa Loading Docks then place a file of the same name, both modules will now use the override file, even if the creatures were originally different. If you are adding new files or even editing existing ones, be cautious of this fact. TSL developers were very guilty of having the same filename across multiple modules.

## Override Tab
The “Override” tab allows you to navigate through the various override files. In TSL you can store files in nested folders and so you can navigate through existing folders using the dropdown menu. This functionality is not present for KotOR 1.

The “Refresh” button will refresh the list of nested folders stored in the override directory.

The “Reload” button will reload the list of resources stored in the selected folder in the dropdown menu. If a resource is changed outside of the toolset, you will need to press this button or an error may occur.

![](images/introduction_1-overrideResources=1.png)
