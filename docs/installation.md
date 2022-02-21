Installation
============

## Loading an Installation
The **Installation** class provides an easy way of loading data from a game directory with minimal coding. To initalize the class, simply pass the path to the root folder for either KotOR or TSL stored on your computer.

```python
installation = Installation("C:/Program Files (x86)/Steam/steamapps/common/swkotor")
```

## Directory detection
The **Installation** class provides methods for determing the various subfolders stored in the game directory. These methods will account for case sensitivity required for Unix-based systems. Paths are determined when the class is initialized.

```python
print( installation.module_path() )
print( installation.override_path() )
print( installation.lips_path() )
print( installation.texturepacks_path() )
print( installation.rims_path() )
print( installation.streammusic_path() )
print( installation.streamsounds_path() )
print( installation.streamvoice_path() )
```

## Loading Resources

### Fetching resource data
Raw data in the form of a bytes object can be extracted from the game with two different methods. One for getting a singular resource and the other for multiple resources.

To fetch the data for a singular resource use the ```resource``` method. This returns a ResourceResult object that extends the NamedTuple class.
```python
resource = installation.resource("appearance", ResourceType.TwoDA)
resname, restype, filepath, data = resource
twoda = load_2da(data)
```

You can narrow your search down and customize the order to look in.
```python
installation.resource("appearance", ResourceType.TwoDA, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
```

You can also specify pass a list of additional folder and module files to search for.
```python
order = [SearchLocation.CHITIN, SearchLocation.CUSTOM_MODULES, SearchLocation.CUSTOM_FOLDERS]
capsules = [Capsule("C:/pathtomodule/module.mod")]
folders = ["C:/pathtofolder"]

installation.resource("somecreature", ResourceType.UTC, order, capsules=capsules, folders=folders)
```

If you wish to look for multiple resources it is more efficient to use the ```resources``` method. This returns a dictionary that maps a ```ResourceIdentifier``` to a ```ResourceResult```.
```python
search = [ResourceIdentifier("appearance", ResourceType.TwoDA), ResourceIdentifier("heads", ResourceType.TwoDA)]
results = installation.resources(search)

appearance = load_2da(results[ResourceIdentifier("appearance", ResourceType.TwoDA)].data)
heads = load_2da(results[ResourceIdentifier("heads", ResourceType.TwoDA)].data)
```

### Finding filepaths
In some situations it might be useful to determine all the locations a resource is specifically present. This can be achieved with ```location()``` or ```locations```. These method's behaviour simularly to the resource methods however use ```LocationResult``` instead of ```ResourceResult```.

```python
location = installation.location("appearance", ResourceType.TwoDA)
filepath, offset, size = location
```

### Loading textures
It is possible to look for a resource and load it directly into a TPC object using ```texture()``` or ```textures()```. This also avoids having to do two searchs with the resource methods as it checks for TPC and TGA ResourceTypes simultaneously.

The single result method behaves simular to ```resource()``` and accepts the same additional parameters. However, the default search locations is slightly different: Extra epecified folders, the override folder, extra specified module files, the TPA texture pack and finally textures linked to the chitin.key file.
```python
installation.texture("C_Gammorean01")
```

The batch texture method behaves slightly differently. Rather than using a standard dict object it uses ```CaseInsensitiveDict``` with string keys rather than ```ResourceIdentifier```.
```python
search = ["C_Gammorean01", "C_GAMMOREAN02"]
textures = installation.textures(search)

tpc1 = textures["c_gammorean01"]
tpc2 = textures["c_gammorean02"]
```