# netcdf-flattener

Flatten netCDF files while preserving references as described in the CF Conventions 1.8, chapter 2.7.

Install dependencies:
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install tqdm
python3 -m pip install --user --upgrade twine

Compile as Pip package:
python3 setup.py bdist_wheel

Install Pip package:
python3 -m pip install dist/netcdf_flattener-0.1-py3-none-any.whl
