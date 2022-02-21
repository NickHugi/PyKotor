PyKotor
=======
A Python library that can read and modify most file formats used by the game Knights of the Old Republic and its sequel.

## Installation
Install from [PyPI](https://pypi.org/project/PyKotor/).
```bash
pip install pykotor
```

## Example Usage
Simple example of loading data from a game directory, searching for a specific texture and exporting it to the TGA format.
```python
import os
from pykotor.resource.type import ResourceType
from pykotor.extract.installation import Installation
from pykotor.resource.formats.tpc import write_tpc

inst = Installation("C:/Program Files (x86)/Steam/steamapps/common/swkotor")
tex = inst.texture("C_Gammorean01")
write_tpc(tex, os.getcwd() + "/C_Gammorean01.tga", ResourceType.TGA)
```

## License
This repository falls under the [MIT License](https://github.com/NickHugi/PyKotor/blob/master/README.md).