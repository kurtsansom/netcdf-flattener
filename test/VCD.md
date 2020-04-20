# Verification Control Document

The document traces the verification of the requirements by tests and other verification methods.

## Methods of verification (MoV)

Requirements are verified using the following methods.
* T: Automated Python test
* RoD: Review of Design

## Traceability matrix

| ID  | Description                                         | Type       | MoV | Reference                                  | Status    |
|-----|-----------------------------------------------------|------------|-----|--------------------------------------------|-----------|
| #1  | Move items in groups into global namespace          | Functional | T   | [test_flatten](test/test_flatten.py)       | Compliant |
| #2  | Apply inherited attributes                          | Functional | T   | [test_flatten](test/test_flatten.py)       | Compliant |
| #3  | Update references following scoping rules in CF-1.8 | Functional | T   | [test_flatten](test/test_flatten.py)       | Compliant |
| #4  | Preserve original names where possible              | Functional | T   | [test_long_names](test/test_long_names.py) | Compliant |
| #5  | Strict by default                                   | Functional | T   | [test_strict_lax](test/test_strict_lax.py) | Compliant |
| #6  | Be stand-alone Python package                       | Packaging  | RoD | [setup.py](setup.py)                       | Compliant |
| #7  | Use Python netCDF4 package from Unidata             | Packaging  | RoD | [setup.py](setup.py#L44)                   | Compliant |
| #8  | Accept netCDF4 I/O                                  | Functional | T   | [test_flatten](test/test_flatten.py)       | Compliant |
| #9  | Preserve original data types                        | Functional | T   | [test_flatten](test/test_flatten.py)       | Compliant |
| #10 | Conform to QA requirements                          | Quality    | RoD | [QA VCD](test/QA_VCD.md)                   | Compliant |
| #11 | Lax mode available                                  | Functional | T   | [test_strict_lax](test/test_strict_lax.py) | Compliant |
| #12 | Documentation as Sphinx project                     | Packaging  | RoD | [doc](doc)                                 | Compliant |
