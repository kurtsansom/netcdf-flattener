# netcdf-flattener

Flatten netCDF files while preserving references as described in the CF Conventions 1.8, chapter 2.7.

## Deployment

### Install dependencies:

`python3 -m pip install --upgrade pip setuptools wheel`

`python3 -m pip install tqdm`

`python3 -m pip install --user --upgrade twine`

### Compile as Pip package:

`python3 setup.py bdist_wheel`

### Install Pip package:

`python3 -m pip install dist/netcdf_flattener-0.1-py3-none-any.whl`

## Automated testing

Running the tests requires having the NetCDF4 libraries installed (ncdump and ncgen applications are required). You can install them either using your package manager, or [build them from the source](https://www.unidata.ucar.edu/software/netcdf/docs/getting_and_building_netcdf.html).

On CentOS: `sudo yum install netcdf `

Install Pytest:

`pip install pytest`

(After this step, you may need to re-activate your virtual environment to make sure that pytest is not going to be run from the local machine)


Run the tests pytests: 

`python3 -m pytest`