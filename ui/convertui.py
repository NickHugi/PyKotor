import glob
import os.path

UI_TARGET_DIR = "../toolset/uic/"
QRC_TARGET_DIR = "../toolset/"


def get_ui_files():
    files = []
    for filepath in glob.iglob("**/*", recursive=True):
        if filepath.endswith(".ui"):
            files.append(filepath)
    return files


def compile_ui(ignore_timestamp: bool = False):
    for ui_source in get_ui_files():
        directory = os.path.dirname(ui_source).replace("\\", "/")
        filename = os.path.basename(ui_source).replace(".ui", ".py")
        ui_target = (UI_TARGET_DIR + directory + "/" + filename).replace("//", "/")

        if not os.path.exists(UI_TARGET_DIR + directory):
            os.makedirs(UI_TARGET_DIR + directory)
            print("mkdir", UI_TARGET_DIR + directory)

        # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
        source_timestamp = os.path.getmtime(ui_source)
        target_timestamp = os.path.getmtime(ui_target) if os.path.exists(ui_target) else 0

        # Only recompile if source file is newer than the existing target file or ignore_timestamp is set to True
        if source_timestamp > target_timestamp or ignore_timestamp:
            command = f"pyuic5 {ui_source} -o {ui_target}"
            os.system(command)
            print(command)


def compile_qrc(ignore_timestamp: bool = False):
    qrc_source = "../resources/resources.qrc"
    qrc_target = QRC_TARGET_DIR + "resources_rc.py"

    # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
    source_timestamp = os.path.getmtime(qrc_source)
    target_timestamp = os.path.getmtime(qrc_target) if os.path.exists(qrc_target) else 0

    # Only recompile if source file is newer than the existing target file or ignore_timestamp is set to True
    if source_timestamp > target_timestamp or ignore_timestamp:
        command = f"pyrcc5 {qrc_source} -o {qrc_target}"
        os.system(command)
        print(command)


if __name__ == "__main__":
    compile_ui()
    compile_qrc()
