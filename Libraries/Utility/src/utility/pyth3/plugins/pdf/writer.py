"""Render documents as Reportlab PDF stories."""
from __future__ import annotations

import cgi  # For escape()

from io import StringIO

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate

from utility.pyth3 import document
from utility.pyth3.format import PythWriter

_tagNames = {"bold": "b",
             "italic": "i",
             "underline": "u",
             "sub": "sub",
             "super": "super"}

LIST_INDENT = 0.3 * inch
BULLET_INDENT = 0.2 * inch
DEFAULT_PARA_SPACE = 0.2 * inch

BULLET_TEXT = "\xe2\x80\xa2"


class PDFWriter(PythWriter):

    @classmethod
    def write(cls, document, target=None, paragraphStyle=None):
        writer = PDFWriter(document, paragraphStyle)
        story = writer.go()

        if target is None:
            target = StringIO()

        doc = SimpleDocTemplate(target)
        doc.build(story)
        return target

    def __init__(self, doc, paragraphStyle=None):
        self.document = doc

        if paragraphStyle is None:
            stylesheet = getSampleStyleSheet()
            paragraphStyle = stylesheet["Normal"]
        self.paragraphStyle = paragraphStyle
        self.paragraphStyle.spaceAfter = 0.2 * inch

        self.paragraphDispatch = {
            document.List: self._list,
            document.Paragraph: self._paragraph}

    def go(self):
        self.paragraphs = []
        for para in self.document.content:
            self._dispatch(para)
        return self.paragraphs

    def _dispatch(self, para, level=0, **kw):
        handler = self.paragraphDispatch[para.__class__]
        return handler(para, level=level, **kw)

    def _paragraph(self, paragraph, level=0, bulletText=None):
        text = "".join(self._text(t) for t in paragraph.content)
        self.paragraphs.append(Paragraph(text, self.paragraphStyle, bulletText=bulletText))

    def _text(self, text) -> str:
        content = cgi.escape("".join(text.content))

        tags = []
        for prop, value in list(text.properties.items()):
            if prop == "url":
                tags.append(('<u><link destination="%s" color="blue">' % value, "</link></u>"))
            if prop in _tagNames:
                tag = _tagNames[prop]
                tags.append(("<%s>" % tag, "</%s>" % tag))

        open_tags = "".join(tag[0] for tag in tags)
        close_tags = "".join(tag[1] for tag in reversed(tags))
        return f"{open_tags}{content}{close_tags}"

    def _list(self, plist, level=0, bulletText=None):
        for entry in plist.content:
            self._list_entry(entry, level=level + 1)

    def _list_entry(self, entry, level):
        first = True
        prevStyle = self.paragraphStyle

        self.paragraphStyle = ParagraphStyle("ListStyle", self.paragraphStyle)

        for para in entry.content:

            if first:
                bullet = BULLET_TEXT
                self.paragraphStyle.leftIndent = LIST_INDENT * level
                self.paragraphStyle.bulletIndent = (LIST_INDENT * level - 1) + BULLET_INDENT
            else:
                bullet = None
                self.paragraphStyle.leftIndent = LIST_INDENT * (level + 1)

            self._dispatch(para, level=level, bulletText=bullet)

            first = False

        self.paragraphStyle = prevStyle



