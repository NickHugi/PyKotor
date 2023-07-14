from pathlib import Path
from typing import List, Optional, Dict

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource, ResourceResult, ResourceIdentifier
from pykotor.resource.formats.erf import ERF, read_erf, write_erf, ERFType
from pykotor.resource.formats.rim import read_rim, write_rim, RIM
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file, is_rim_file, is_erf_file

class Capsule:
    """
    Chitin object is used for loading the list of resources stored in the .erf/.rim/.mod files used by the game.
    Resource data is not actually stored in memory by default but is instead loaded up on demand with the
    Capsule.resource() method.
    """
    def __init__(
            self,
            path: Path,
            create_nonexisting: bool = False
    ):
        self._path: Path = Path(path)
        self._resources: List[FileResource] = []

        if not is_capsule_file(path.name):
            raise ValueError(f"Invalid file extension in capsule filepath '{path}'.")

        if create_nonexisting and not path.exists:
            if is_rim_file(path.name):
                write_rim(RIM(), path)
            elif is_erf_file(path.name):
                write_erf(ERF(ERFType.from_extension(path)), path)

        self.reload()

    def __iter__(
            self
    ):
        yield from self._resources

    def __len__(
            self
    ):
        return len(self._resources)

    def resource(
            self,
            resref: str,
            restype: ResourceType,
            reload: bool = False
    ) -> Optional[bytes]:
        """
        Returns the bytes data of the specified resource. If the resource does not exist then returns None instead.

        Args:
            resref: The resource ResRef.
            restype: The resource type.
            reload: If True Capsule will reload the ERF before opening rather than using cached offsets.

        Returns:
            None or bytes data of resource.
        """
        resource = self._extracted_from_info_18(reload, resref, restype)
        return None if resource is None else resource.data()

    def batch(
            self,
            queries: List[ResourceIdentifier],
            reload: bool = False
    ) -> Dict[ResourceIdentifier, Optional[ResourceResult]]:
        """
        The `batch` function takes a list of resource identifiers, optionally reloads the resources, and
        returns a dictionary of resource results.
        
        :param queries: The `queries` parameter is a list of `ResourceIdentifier` objects. Each
        `ResourceIdentifier` object represents a resource that you want to retrieve from a batch of
        resources
        :type queries: List[ResourceIdentifier]
        :param reload: The `reload` parameter is a boolean flag that indicates whether the resources
        should be reloaded from the file before processing the queries. If `reload` is set to `True`,
        the `reload()` method of the class is called to reload the resources. If `reload` is set to
        `False, defaults to False
        :type reload: bool (optional)
        :return: The function `batch` returns a dictionary where the keys are `ResourceIdentifier`
        objects and the values are `ResourceResult` objects or `None`.
        """
        if reload:
            self.reload()

        results = {}
        reader = BinaryReader.from_file(self.path())

        for query in queries:
            results[query] = None
            if self.exists(query.resname, query.restype):
                resource = next((resource for resource in self._resources if resource == query), None)
                if resource is not None:
                    reader.seek(resource.offset())
                    data = reader.read_bytes(resource.size())
                    results[query] = ResourceResult(query.resname, query.restype, self.path(), data)

        reader.close()
        return results

    def exists(
            self,
            resref: str,
            restype: ResourceType,
            reload: bool = False
    ) -> bool:
        """
        The `exists` function checks if a resource with a given reference and type exists, and
        optionally reloads it if specified.
        
        :param resref: The `resref` parameter is a string that represents the reference name of the
        resource you want to check for existence. It is typically used to uniquely identify a resource
        within a system or application
        :type resref: str
        :param restype: The `restype` parameter is of type `ResourceType`. It is used to specify the
        type of resource you are checking for existence
        :type restype: ResourceType
        :param reload: The `reload` parameter is a boolean flag that indicates whether the resource
        should be reloaded from disk or not. If `reload` is set to `True`, the resource will be reloaded
        even if it has already been loaded before. If `reload` is set to `False` (default, defaults to
        False
        :type reload: bool (optional)
        :return: a boolean value.
        """
        resource = self._extracted_from_info_18(reload, resref, restype)
        return resource is not None

    def info(
            self,
            resref: str,
            restype: ResourceType,
            reload: bool = False
    ) -> FileResource:
        """
        The "info" function takes in a resource reference, resource type, and an optional reload flag,
        and returns a FileResource object.
        
        :param resref: The `resref` parameter is a string that represents the reference name of the
        resource. It is used to uniquely identify the resource within a system or application
        :type resref: str
        :param restype: The `restype` parameter is of type `ResourceType`. It is used to specify the
        type of resource that is being requested
        :type restype: ResourceType
        :param reload: The `reload` parameter is a boolean flag that indicates whether the resource
        should be reloaded from disk or not. If `reload` is set to `True`, the resource will be reloaded
        from disk even if it has already been loaded before. If `reload` is set to `False`, defaults to
        False
        :type reload: bool (optional)
        :return: a FileResource object.
        """
        return self._extracted_from_info_18(reload, resref, restype)

    # TODO Rename this here and in `resource`, `exists` and `info`
    def _extracted_from_info_18(self, reload, resref, restype):
        if reload:
            self.reload()
        query = ResourceIdentifier(resref, restype)
        result = next((result for result in self._resources if result == query), None)
        return result

    def reload(
            self
    ):
        """
        Reload the list of resource info linked from the module file.
        """
        with BinaryReader.from_file(self._path) as reader:
            file_type = reader.read_string(4)
            file_version = reader.read_string(4)

            if file_type in ("ERF ", "MOD "):
                self._load_erf(reader)
            elif file_type == "RIM ":
                self._load_rim(reader)
            else:
                raise ValueError(f"File '{self._path}' was not an ERF/MOD/RIM.")

    def add(
            self,
            resname: str,
            restype: ResourceType,
            resdata: bytes
    ):
        """
        The function adds a resource to a container file, either in RIM or ERF format.
        
        :param resname: The `resname` parameter is a string that represents the name of the resource you
        want to add
        :type resname: str
        :param restype: The parameter "restype" is of type "ResourceType". It is used to specify the
        type of the resource being added
        :type restype: ResourceType
        :param resdata: The parameter `resdata` is of type `bytes` and represents the data of the
        resource that you want to add to the container
        :type resdata: bytes
        """
        container = read_rim(self._path.name) if is_rim_file(self._path.name) else read_erf(self._path)
        container.set(resname, restype, resdata)
        write_rim(container, self._path) if is_rim_file(self._path.name) else write_erf(container, self._path)

    def path(
        self
    ) -> Path:
        """
        The function returns the path attribute of an object.
        :return: The method is returning the value of the `_path` attribute.
        """
        return self._path

    def filename(
            self
    ) -> str:
        return self._path.name

    def _load_erf(
            self,
            reader: BinaryReader
    ):
        reader.skip(8)
        entry_count = reader.read_uint32()
        reader.skip(4)
        offset_to_keys = reader.read_uint32()
        offset_to_resources = reader.read_uint32()

        resrefs = []
        resids = []
        restypes = []
        reader.seek(offset_to_keys)
        for _ in range(entry_count):
            resrefs.append(reader.read_string(16))
            resids.append(reader.read_uint32())
            restypes.append(ResourceType.from_id(reader.read_uint16()))
            reader.skip(2)

        reader.seek(offset_to_resources)
        for i in range(entry_count):
            res_offset = reader.read_uint32()
            res_size = reader.read_uint32()
            self._resources.append(FileResource(resrefs[i], restypes[i], res_size, res_offset, self._path))

    def _load_rim(
            self,
            reader: BinaryReader
    ):
        reader.skip(4)
        entry_count = reader.read_uint32()
        offset_to_entries = reader.read_uint32()

        reader.seek(offset_to_entries)
        for _ in range(entry_count):
            resref = reader.read_string(16)
            restype = ResourceType.from_id(reader.read_uint32())
            res_id = reader.read_uint32()
            offset = reader.read_uint32()
            size = reader.read_uint32()
            self._resources.append(FileResource(resref, restype, size, offset, self._path))

