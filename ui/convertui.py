import glob

import os.path

target_dir = "../toolset/"

for filepath in glob.iglob("**/*", recursive=True):
    if filepath.endswith(".ui"):
        directory = os.path.dirname(filepath).replace("\\", "/")
        filename = "" + os.path.basename(filepath).replace(".ui", ".py")
        new_path = (target_dir + "/uic/" + directory + "/" + filename).replace('//', '/')
        print(new_path, target_dir, directory)
        os.system("pyuic5 {} -o {}".format(filepath, new_path))


qrc_path = "../resources/resources.qrc"
qrc_target = target_dir + "resources_rc.py"
os.system("pyrcc5 {} -o {}".format(qrc_path, qrc_target))
