# netcdf-flattener

Flatten netCDF files while preserving references as described in the CF Conventions 1.8, chapter 2.7.

## Usage
To flatten the Netcdf file named *"input_file.nc"* into a new file named *"output_file.nc"*, use the following command.

    import netcdf_flattener
    netcdf_flattener.flatten("input_file.nc", "output_file.nc")

By default, the flattener is in strict mode and returns an exception if a an internal reference from a variable 
attribute to a dimension or variable could not be resolved. To use the lax mode that continues the flattening process 
with warning, specify the `lax_mode` parameter:

    netcdf_flattener.flatten("input_file.nc", "output_file.nc", lax_mode=True)

## Deployment

Install the build dependencies:

    python3 -m pip install --upgrade pip setuptools wheel

To compile the wheel file, run the following command from the repository root:

    python3 setup.py bdist_wheel

Install the wheel file using PIP:

    python3 -m pip install dist/netcdf_flattener-*.whl

## Automated testing

### Dependencies

Running the tests requires having the NetCDF4 libraries installed (ncdump and ncgen applications are required). You can 
install them either using your package manager, or 
[build them from the source](https://www.unidata.ucar.edu/software/netcdf/docs/getting_and_building_netcdf.html).

On CentOS: `sudo yum install netcdf `

Install Pytest:

    python3 -m pip install pytest
    
All other dependencies are managed by pip and use OSI-approved licenses.

### Run the tests

Run Pytest from the root of the repository: 

    python3 -m pytest

## Documentation

A Sphinx project is provided to generate the HTML documentation from the code.

Install Sphinx: 

    python3 -m pip install sphinx

From the "doc" folder, build the documentation:

    cd doc
    sphinx-build -b html . build

The entry point to the documentation is the doc/build/index.html file.

## License

This code is under Apache 2.0 License. See [LICENSE](LICENSE) for the full license text.

## Authors

See [AUTHORS](AUTHORS.md) for details.
