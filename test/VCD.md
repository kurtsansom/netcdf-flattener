# VCD

## Methods of verification

T: Automated Python test

## Traceability matrix

| ID  | Description                                         | Type       | MoV | Reference       | Status    |
|-----|-----------------------------------------------------|------------|-----|-----------------|-----------|
| #1  | Move items in groups into global namespace          | Functional | T   | test_flatten    | Compliant |
| #2  | Apply inherited attributes                          | Functional | T   | test_flatten    | Compliant |
| #3  | Update references following scoping rules in CF-1.8 | Functional | T   | test_flatten    | Compliant |
| #4  | Preserve original names where possible              | Functional | T   | test_long_names | Compliant |
| #5  | Strict by default                                   | Functional | T   | test_strict_lax | Compliant |
| #6  | Be stand-alone Python package                       | Packaging  |     |                 | Compliant |
| #7  | Use Python netCDF4 package from Unidata             | Packaging  |     |                 | Compliant |
| #8  | Accept netCDF4 I/O                                  | Functional | T   | test_flatten    | Compliant |
| #9  | Preserve original data types                        | Functional | T   | test_flatten    | Compliant |
| #10 | Conform to QA requirements                          | Quality    |     |                 | Compliant |
| #11 | Lax mode available                                  | Functional | T   | test_strict_lax | Compliant |
| #12 | Documentation as Sphinx project                     | Packaging  |     |                 | Compliant |
