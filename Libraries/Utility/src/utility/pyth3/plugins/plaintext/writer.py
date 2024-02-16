"""Render documents as plaintext."""
from __future__ import annotations

from io import StringIO
from typing import Any

from utility.pyth3 import document
from utility.pyth3.format import PythWriter


class PlaintextWriter(PythWriter):

    @classmethod
    def write(cls, document, target=None, newline="\n") -> StringIO | Any:
        if target is None:
            target = StringIO()

        writer = PlaintextWriter(document, target, newline)
        return writer.go()


    def __init__(self, doc, target, newline):
        self.document = doc
        self.target = target
        self.newline = newline
        self.indent = -1
        self.paragraphDispatch = {
            document.List: self.list,
            document.Paragraph: self.paragraph
        }


    def go(self):
        for (_i, paragraph) in enumerate(self.document.content):
            handler = self.paragraphDispatch[paragraph.__class__]
            handler(paragraph)
            self.target.write("\n")

        # Heh heh, remove final paragraph spacing
        self.target.seek(-2, 1)
        self.target.truncate()

        self.target.seek(0)
        return self.target


    def paragraph(self, paragraph: document.Paragraph, prefix: str = ""):
        content_list = ["".join(text.content) for text in paragraph.content]
        content = "".join(content_list)
        for line in content.split("\n"):
            self.target.write("  " * self.indent)
            self.target.write(prefix)
            self.target.write(line)
            self.target.write("\n")
            if prefix:
                prefix = "  "


    def list(self, list, prefix=None):
        self.indent += 1
        for (_i, entry) in enumerate(list.content):
            for (j, paragraph) in enumerate(entry.content):
                prefix = "* " if j == 0 else "  "
                handler = self.paragraphDispatch[paragraph.__class__]
                handler(paragraph, prefix)
        self.indent -= 1





