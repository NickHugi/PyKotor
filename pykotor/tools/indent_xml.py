from xml.etree.ElementTree import Element


def indent(elem: Element, level=0):
    """Indents the XML element by the given level
    Args:
        elem: Element - The element to indent
        level: int - The level of indentation (default: 0).

    Returns
    -------
        None - Indents the element in-place
    Processing Logic:
        - Calculate indentation string based on level
        - If element is empty, set text to indentation
        - If no tail, set tail to newline + indentation
        - Recursively indent child elements with increased level
        - If no tail after children, set tail to indentation
        - If level and no tail, set tail to indentation.
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = f"{i}  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for e in elem:
            indent(e, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    elif level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i
