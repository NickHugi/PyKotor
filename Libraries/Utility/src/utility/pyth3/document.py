"""Abstract document representation."""

from __future__ import annotations


class _PythBase:
    validProperties: tuple[str, ...] = ()
    contentType: type

    def __init__(self, properties: dict | None = None, content: list | None = None):
        if properties is None:
            properties = {}
        if content is None:
            content = []
        self.properties: dict = {}
        self.content: list = []

        for k, v in properties.items():
            self[k] = v

        for item in content:
            self.append(item)

    def __setitem__(self, key, value):
        if key not in self.validProperties:
            msg = f"Invalid {self.__class__.__name__} property: {key!r}"
            raise ValueError(msg)

        self.properties[key] = value

    def __getitem__(self, key):
        if key not in self.validProperties:
            msg = f"Invalid {self.__class__.__name__} property: {key!r}"
            raise ValueError(msg)
        return self.properties.get(key)

    def append(self, item):
        """Try to add an item to this element.

        If the item is of the wrong type, and if this element has a sub-type,
        then try to create such a sub-type and insert the item into that, instead.

        This happens recursively, so (in python-markup):
          L [ u'Foo' ]
        actually creates:
          L [ LE [ P [ T [ u'Foo' ] ] ] ]

        If that doesn't work, raise a TypeError.
        """
        okay = True
        if not isinstance(item, self.contentType):
            if hasattr(self.contentType, "contentType"):
                try:
                    item = self.contentType(content=[item])
                except TypeError:
                    okay = False
            else:
                okay = False

        if not okay:
            msg = f"Wrong content type for {self.__class__.__name__}: {item.__class__!r} ({item!r})"
            raise TypeError(msg)

        self.content.append(item)


class Text(_PythBase):
    """Text runs are strings of text with markup properties,
    like 'bold' or 'italic' (or 'hyperlink to ...').

    They are rendered inline (not as blocks).

    They do not inherit their properties from anything.
    """

    validProperties = ("bold", "italic", "underline", "url", "sub", "super")
    contentType = str

    def __repr__(self):
        return f"""Text('{"".join(f'[{r.encode("utf-8")}]' for r in self.content)}' {self.properties})"""


class Paragraph(_PythBase):
    """Paragraphs contain zero or more text runs.

    They cannot contain other paragraphs (but see List).

    They have no text markup properties, but may
    have rendering properties (e.g. margins)
    """

    validProperties: tuple = ()
    contentType = Text


class Image(Paragraph):
    """An image is stored in bytes. All properties of images from the rtf definition are allowed."""

    validProperties = (
        "emfblip",
        "pngblip",
        "jpegblip",
        "macpict",
        "pmmetafile",
        "wmetafile",
        "dibitmap",
        "wbitmap",
        "wbmbitspixel",
        "wbmplanes",
        "wbmwidthbytes",
        "picw",
        "pich",
        "picwgoal",
        "pichgoal",
        "picscalex",
        "picscaley",
        "picscaled",
        "piccropt",
        "piccropb",
        "piccropr",
        "piccropl",
        "picbmp",
        "picbpp",
        "bin",
        "blipupi",
        "blipuid",
        "bliptag",
        "wbitmap",
    )
    contentType = bytes

    def __repr__(self):
        return "Image(%d bytes, %s)" % (len(self.content[0]) / 2, self.properties)


class ListEntry(_PythBase):
    """A list of paragraphs representing one item in a list."""

    validProperties = ()
    contentType = Paragraph


class List(Paragraph):
    """A list of paragraphs which will be rendered as a bullet list.

    A List is a Paragraph, so Lists can be nested.
    """

    validProperties = ()
    contentType = ListEntry


class Document(_PythBase):
    """Top-level item. One document is exactly one file.
    Documents consist of a list of paragraphs.
    """

    validProperties = ("title", "subject", "author")
    contentType = Paragraph
