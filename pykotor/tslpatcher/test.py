from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods import twoda
from pykotor.tslpatcher.reader import ConfigReader

tslreader = ConfigReader.from_filepath("C:\\Users\\boden\\Documents\\tsl mods\\High Level Force Powers V2u1\\tslpatchdata\\changes.ini")
tslreader.load_2da_list()
tslreader.load_settings()
tslreader.load_tlk_list()
tslreader.load_install_list()
tslreader.load_2da_list()
tslreader.load_gff_list()
tslreader.load_compile_list()
tslreader.load_ssf_list()
memory = PatcherMemory()
tslreader.config.patches_tlk.execute_patch(r"C:\Program Files (x86)\Steam\steamapps\common\Knights of the Old Republic II\dialog.tlk", memory)
for patch in tslreader.config.patches_2da:
    twoda.Modifications2DA.execute_patch(patch, r"C:\Users\boden\Documents\tsl mods\High Level Force Powers V2u1\tslpatchdata\effecticon.2da", memory)
print("2DAMEMORY:", *memory.memory_2da)
print("STRREF:", *memory.memory_str)
