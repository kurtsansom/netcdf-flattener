# Release notes
All notable changes to this project will be documented in this file.

## Pending
- Allow flattening files without copying variables
- Issue #25: Centralize versioning in __init__.py file
- Issue #25: Add contribution rules and MR template

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
