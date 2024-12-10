# Conventions

- Use types everywhere possible.
- Give attributes types in __init__ immediately.
- Wrap each arg to a newline in a function if it has more than 2 args.
- Don't use title-case types from the typing module, this includes Optional and Union. Use `from __future__ import annotations` to allow type hints to be evaluated at runtime (e.g. `str | None`).
- Prefer fast-exit functions over nested conditionals.
- Consider how the program will continue if an exception is raised unexpectedly, and ensure that it does so gracefully.
- (if using qt in python) always import from qtpy.QtWidgets, qtpy.QtGui, and qtpy.QtCore etc.
