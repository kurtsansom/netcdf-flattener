# Release notes
All notable changes to this project will be documented in this file.

## Pending
- #26: Use `logging.info` rather than `print`
- Allow flattening files without copying variables
- Issue #24: Allow copying large variables in slices
- Issue #25: Centralize versioning in __init__.py file
- Issue #25: Add contribution rules and MR template
- Issue #27: Some coordinate variables lose assocation with data variables upon flattening
- Issue #29: Replace `#` by `__` in flattened names for CF compliance
- Refactoring parsing of references in attributes: 
  - Issue #28: Add support for expanded form of `grid_mapping` attribute
  - Issue #30: Add support for attribute values in the form `y: x: mean (interval: 1 degree comment: comment 1 here) t: 
maximum (comment 2 here)`. 
  - Issue #30: For `cell_methods`, only accept references to variables that are scalar coordinate variables.
- Issue #23: prefix flattener-related attributes with double underscore.

## 1.0.1
- Issue #8: Correct API to use `Dataset` objects as I/O instead of filenames.
- Issue #21:
  - Fix issue with some references to dimensions/variables in the root group
  not being resolved.
  - Make the `cell_methods` attribute a special case, which can contain a
  reference to a coordinate variable, a reference to a dimension, the keyword
  `area`, or any standard name.

## 1.0.0
- First release.
