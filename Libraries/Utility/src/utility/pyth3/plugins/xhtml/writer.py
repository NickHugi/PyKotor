"""Render documents as XHTML fragments."""
from __future__ import annotations

from io import StringIO

from utility.pyth3 import document
from utility.pyth3.format import PythWriter

_tagNames = {
    "bold": "strong",
    "italic": "em",
    "underline": "u",  # ?
}


class XHTMLWriter(PythWriter):

    @classmethod
    def write(klass, document, target=None, cssClasses=True, pretty=False):
        if target is None:
            target = StringIO()

        writer = XHTMLWriter(document, target, cssClasses, pretty)
        final = writer.go()
        final.seek(0)

        # Doesn't work all that well -- appends an <?xml ...> tag,
        # and puts line breaks in unusual places for HTML.
        # if pretty:
        #    content = final.read()
        #    final.seek(0)
        #    from xml.dom.ext import PrettyPrint
        #    from xml.dom.ext.reader.Sax import FromXml
        #    PrettyPrint(FromXml(content), final)
        #    final.seek(0)

        return final

    def __init__(self, doc, target, cssClasses=True, pretty=False):
        self.document = doc
        self.target = target
        self.cssClasses = cssClasses
        self.pretty = pretty
        self.paragraphDispatch = {
            document.List: self._list,
            document.Paragraph: self._paragraph
        }

    def go(self):

        self.list_level = -1

        tag = Tag("div")

        for element in self.document.content:
            handler = self.paragraphDispatch[element.__class__]
            tag.content.extend(handler(element))

        tag.render(self.target)
        return self.target

    def _paragraph(self, paragraph):
        p = Tag("p")
        for text in paragraph.content:
            p.content.append(self._text(text))

        if self.pretty:
            return [_prettyBreak, p, _prettyBreak]
        return [p]

    def _list(self, lst):
        self.list_level += 1

        ul = Tag("ul")

        if self.cssClasses:
            ul.attrs["class"] = "pyth_list_%s" % self.list_level

        for entry in lst.content:
            li = Tag("li")
            for element in entry.content:
                handler = self.paragraphDispatch[element.__class__]
                li.content.extend(handler(element))
            ul.content.append(li)

        self.list_level -= 1

        return [ul]

    def _text(self, text):
        if "url" in text.properties:
            tag = Tag("a")
            tag.attrs["href"] = text.properties["url"]
        else:
            tag = Tag(None)

        current = tag

        for prop in ("bold", "italic", "underline"):
            if prop in text.properties:
                newTag = Tag(_tagNames[prop])
                current.content.append(newTag)
                current = newTag

        for prop in ("sub", "super"):
            if prop in text.properties:
                if current.tag is None:
                    newTag = Tag("span")
                    current.content.append(newTag)
                    current = newTag
                current.attrs["style"] = "vertical-align: %s; font-size: smaller" % prop

        current.content.append("".join(text.content))

        return tag


_prettyBreak = object()


class Tag:

    def __init__(self, tag, attrs=None, content=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.content = content or []

    def render(self, target):

        if self.tag is not None:
            attrString = self.attrString()
            if attrString:
                attrString = " " + attrString
            target.write(f"<{self.tag}{attrString}>")

        for c in self.content:
            if isinstance(c, Tag):
                c.render(target)
            elif c is _prettyBreak:
                target.write("\n")
            else:
                target.write(quoteText(c).encode("utf-8").replace("\n", "<br />"))

        if self.tag is not None:
            target.write("</%s>" % self.tag)

    def attrString(self):
        return " ".join(
            f'{k}="{quoteAttr(v)}"'
            for (k, v) in self.attrs.items())

    def __repr__(self):
        return f"T({self.tag})[{self.content!r}]"


def quoteText(text):
    return text.replace(
        "&", "&amp;").replace(
        "<", "&lt;").replace(
        ">", "&gt;")


def quoteAttr(text):
    return quoteText(text).replace(
        '"', "&quot;").replace(
        "'", "&apos;")
