Cameras in the KotOR games are rather simple once you get the hang of
them, but before I start explaining much let’s do a quick overview on
what cameras are.

*Cameras: Static viewpoints that you can setup at any given location in
an area. They provide you the freedom to make in-game dialogue into more
than just a sequence of talking. For the purpose of this tutorial
cameras will only refer to static cameras, not animated cameras.*

Prior to starting any kind of modding you’ll want the proper tools for
what you’re doing. So, without further delay, here are the five things
you’ll need to make a camera.

1.  

2.  ( for those interested, the download link there is down)

3.  K1 Utility Armbands

for the armbands. All credit goes to Star Admiral for the creation of

the utility armbands, I just modified his script to include two new
fields necessary to

orienting the cameras correctly. I also modified his setup of the
installer to work for KotOR

2 as well.

Make sure all these tools are installed and ready for use before
beginning this tutorial. K1 Utility Armbands is a mod, so therefore it
will install into the game’s directory via the TSL Patcher but it is
still necessary to have installed in order to follow this tutorial. You
will need cheats enabled for this tutorial. I recommend to walk you
through the process of enabling them. Also, to be clear, this tutorial
covers static cameras only. Animated cameras are not covered at all.

Before you start making your camera, you’ll have to extract all the
files from the game that are necessary for its creation.

So, open up KotOR Tool. Depending on which game you wish to edit, expand
the KotOR 1 tree or the KotOR 2 tree. I’ll be editing KotOR 1 for this
tutorial, so I’m going to expand that one.

After you’ve expanded your game’s tree, expand RIMs, then Modules. From
there you’ll be presented with a list of modules found within the game.
The module names displayed here are the game files’ actual names. To
help with matching these names to the areas you visit in-game, I
recommend looking , and .

You’re going to need to expand the module name which is not followed by
an “\_s” (without the quotes, of course). I’m editing Manaan Ahto West
for this tutorial so I expanded manm26aa.rim.

From there you want to expand Dynamic Area Info. There you’ll see a GIT
file, the base file in which a camera’s information - and many other
bits of data pertaining to a module - is stored.

Extract it to a directory of your choice (I recommend a folder titled
Module GIT File).

Next, you’re going to want to create a folder in the directory where the
extracted GIT file is. Name this folder “Original Module Files.”

Once that is done, you’ll want to select the .rim and extract the entire
RIM file to your newly created Original Module Files folder. Repeat this
step for the \_s part of the module you’re editing (in my case,
manm26aa_s.rim).

Now, you’re going to want to open up the GIT file you extracted with
tk102’s K-GFF editor. When your GIT file is open, I recommend you fold
all trees by going to View -\> Fold All, and then only expand the struct
labeled CameraList.

Below you’ll find the layout of a GIT file’s generic camera entry that
can be found under CameraList.

CameraList is, as you’d imagine, a grouping of all the cameras contained
within this one GIT file. The cameras are then separated into STRUCT’s.
Now contained within any camera’s STRUCT, you have six fields that flesh
out the identity of this individual camera.

CameraID – This is a numeric value given to your camera so it can be
used later in a dialogue file. This number can go anywhere from one to
infinity, I imagine, but I’ve never had a module go above one hundred
cameras. Also, I’d endeavor to make sure this ID is unique – I’ve never
had a module where two separate cameras used the same CameraID, but I’m
guessing it wouldn’t be pretty.

FieldOfView – Another numeric value, this acts similar to a zoom
setting, allowing you to give the camera a larger space to look at,
without moving its actual location. I don’t mess around with this too
much, and the few times I did set it to an extreme, like one hundred,
the camera’s view looked odd. I generally keep FieldOfView in the
fifty-five to sixty-five range.

Height – This gets added on to whatever you set as the value for the Z
coordinate in position (more on position later). I find the average
height of a person in the KotOR games tends to be around 1.5 so I
generally set most cameras to have a height nearer to that number.

Orientation –

Here is a picture of a basic orientation field:

Now this is the part about cameras that got under my skin when I was
first learning to use them. Essentially, as you can see above, the
orientation requires two numbers. However, KotOR apparently uses
quaternions (weird number value used nowhere else in the game) to
calculate the orientation for static cameras and I, for the life of me,
had never been able to get the orientation to work very well when first
starting out. So, I eventually became frustrated enough with guessing
and checking that I added a little bit to the orientation armband’s
scripting (from K1 Utility Armbands) in order to give me the correct
values to input into the orientation fields (more on that later).

Pitch – This one’s rather simple. It’s just a numerical value that
determines if the camera is pointing up, down, or straight. It can range
anywhere from 0 to 180, with 0 being straight down, 90 being straight
ahead and 180 being directly up. The range might even go beyond 180, or
below 0, but I’ve never tried that.

Position -

Here is a picture of a basic position field:

Position, as you can see, has three slots. The top is the X coordinate,
the middle is the Y coordinate and the bottom is the Z coordinate. You
enter a specific value for each one, depending on where you want the
camera located in the area.

Usually, whenever you create a camera you’ll want to select the whole
STRUCT and copy it. Then, select the CameraList and paste it. This is a
fast way to give you a camera which won’t override any of the existing
ones, providing you change the camera ID number.

All right, now that we’ve gone through the basics of the GIT’s camera
layout, let’s move onto actually creating a camera.

To start off you, you’re going to want to get all the information
necessary from the game, so fire up whichever KotOR you’re modding. When
you first get into the area you want a camera, make sure to enter in
this cheat “giveitem sa_ori_arm” minus the quotes, of course. This will
give you the orientation armband. When activated, this armband gives you
tons of information about the playing character’s position, angle
orientation, bearing, X and Y orientation, distance from other objects,
closest types of objects to the player, etcetera.

(NOTE: The armband gives you the information about the PLAYING
character. This means your character that you name and play the game as
for the most part. As it is setup currently, if a party member were to
use the armband it would still shoot back the player’s information.)

So, as you can see below I’m on Manaan, talking to my trusty, and very
enduring, friend Trask Ulgo.

Now, say I wanted to have a camera set up facing that Sith Officer
standing next to me, I’d need to walk over there, face her, and then use
the orientation armband.

To face the way you want the camera to face, I recommend going into
first person mode by pressing caps-lock, or whatever key you have it as,
and moving around until the center of the screen is where you want the
center of the camera to be.

It’s very important to remember that when the orientation armband gives
you the orientation, it is NOT the orientation of the third person
camera, but the actual direction the player model is facing (I made this
mistake when first using the orientation armband).

Anyway, so once you’re off and facing the way you want your camera to
face you should equip the orientation armband and use it (it equips just
like an energy shield is and is used like one).

After using the armband, you’ll need to recover the information it has
gathered by going to the Feedback screen. This can be found by going to
the messages screen in the menu, then clicking on show feedback.

In the show feedback screen, as you can see above, it says that my
poorly random-name-generated character has used the orientation armband
and then it begins the output, showing you all kinds of information.
We’re currently interested in only three things however: player
position, quaternion X and quaternion Y.

(NOTE: The quaternion inputs are only available with the custom version
of the utility armbands which has a download link at the top of the
tutorial.)

Player location is shown in the screen above, as is quaternion X, but
we’re going to need to scroll down for the Y.

Now that we’ve gotten all the inputs needed for the orientation of the
camera it’s time to go back to the GIT file and enter the information.
Copy a preexisting camera STRUCT and paste it, as described earlier, to
give you your own camera. Find the orientation field, then enter in the
quaternion X orientation into the top box and the quaternion Y
orientation into the bottom, such as below.

Now the position information is given to you as a set of three numbers,
in my case:

-67.875 -3.850 57.50

These numbers are the X, Y, and Z coordinates, respectively. Enter them
into the GIT field, X going into the top slot, Y into the middle and Z
into the bottom, as it is below.

Next we’ll do all the other fields that don’t really require information
from the armband:

CameraID – I’d make this number one higher than the ID of the last
camera in the module (i.e., if the camera found above yours in the
CameraList has an ID of 9, make your camera’s ID 10. My camera ID in
this case actually is 10).

FieldOfView – Again, as I said earlier, generally keep FieldOfView
between 55 and 65. For this one I’ll just leave it at 65.

Height – I usually set this at about 1.5, because I find that amounts to
the average height of a person in the KotOR’s. Depending on what you
want to do though, this may be much higher or lower.

Pitch – I’m going to have mine at 90, because I want my camera facing
straight ahead (0 makes the camera look directly down and 180 makes it
look directly up).

Okay, so you’re finished with the GIT, save it and close K-GFF (or leave
it open, if you prefer).

On to the dialogue portion!

Putting the camera into dialogue is really simple actually. You setup
your scene/conversation in the DLG Editor and when you’re done, you can
go back through and add in all your camera entries. In my case I only
have one camera I’ll be using, and it’s for testing purposes, so my
dialogue looks like the picture below (for those that need a
comprehensive tutorial on how to setup dialogues, I recommend and to
cover most of the basics).

To enter in your camera, select the node you want to edit. Then, change
the CameraID field to your camera’s ID field, and the camera angle to 6,
as it is shown below (the camera angle for static cameras must ALWAYS be
6).

You might want to add a delay on there too, depending on what you’re
doing with the camera. I set my delay to 30, so I’d be sure that I would
have enough time to look at the camera and make sure it was setup
properly. When you’re done setting up your dialogue save it.

Now open up stoffe’s ERF editor.

We’re going to use stoffe’s ERF editor to create a .MOD file. .MOD files
are used to “override” the original information for the module that was
found within your module’s two .RIM files (in my case, manm26aa.rim and
manm26aa_s.rim) with your newly modified information. I put override in
quotes because the two original files themselves are never actually
replaced (and they never should be). The game uses a .MOD file above a
.RIM file to load a module when you’re playing the game. If a .MOD
exists, it ignores the two .RIM files, essentially. This allows you to
“override” the original game without actually deleting or replacing the
game’s original files.

So, on to creating your .MOD.

Go to the File menu in the ERF editor, then hit new (or just press
Ctrl+N).

This will cause a Save As dialogue box to pop up. Navigate to the
directory where your GIT file, and your Original Module Files folder, is
located. Make the file name the same name as the module you’re editing
(in my case, manm26aa) and change the save as type from ERF file to
Module file. Then hit save.

Now because there are no files in your new .MOD, no .MOD file will show
up in your directory. So, the next step is adding all the files. Click
the Add Resources to this File button.

This will cause an Open dialogue box to pop up. Navigate to the Original
Module Files folder you created earlier, and open it. Once there, select
all the files inside it and click the open button in the dialogue box.
Then save the .MOD.

This will cause your .MOD to be filled with all the files from both the
module’s .RIM’s.

Now you want to add in your modified files. Select the add resources
button again and navigate to where your GIT file and dialogue file are.
Add them both to the .MOD

(If your dialogue is just for testing purposes, like mine, you’ll
probably want to put it in the override).

Take your newly-saved .MOD and put it in the modules folder
(SWKotOR/SWKotOR2 -\> Modules).

Go in game and make your way to the module you’ve added the camera to.

(NOTE: You MUST load a save from before having entered the area in order
for your camera to actually show up.)

Your camera should now show up within your dialogue.

That’s all there is to it.
