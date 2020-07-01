# netcdf-flattener

Flatten netCDF files while preserving references as described in the CF Conventions 1.8, chapter 2.7.

## Usage
The flattener takes as input and output NetCDF *Dataset* objects, which the user can create or open from *".nc"* files 
using the netCDF4 API. To flatten the Dataset named *"input_dataset"* into a Dataset named *"output_dataset"*, use the 
following command. In most cases, *"output_dataset"* will be an empty Dataset.

    import netcdf_flattener
    netcdf_flattener.flatten(input_dataset, output_dataset)

By default, the flattener is in strict mode and returns an exception if a an internal reference from a variable 
attribute to a dimension or variable could not be resolved. To use the lax mode that continues the flattening process 
with warning, specify the `lax_mode` parameter:

    netcdf_flattener.flatten(input_dataset, output_dataset, lax_mode=True)

For copying variables that would otherwise be larger than the available memory, the `copy_slices` parameter allows to 
specify slices to be used when copying the variable. They are specified per variable in a dictionary. The slicing shape 
is either `None` for using a default slice value, or a custom slicing shape in the form of a tuple of the same dimension 
as the variable. If a variable from the Dataset is not contained in the dict, it will not be sliced and copied normally.

Slice shapes should be small enough to fit in memory, but not too small larges loops on small slice can degrade 
performances drastically. Typically, slices of size in the order of 10^6 to 10^8 are suitable. 

    netcdf_flattener.flatten(input_dataset, output_dataset, copy_slices={"/grp1/var1": (1000,1000,500,), "/grp1/var3": None})

### Limitations    

When a CF coordinate variable in the input dataset is in a different
group to its corresponding dimension, the same variable in the output
flattened dataset will *no longer* be a CF coordinate variable, as its
name will be prefixed with a different group identifier than its
dimension. In such cases, it is up to the user to apply the [proximal
and lateral search alogrithms](https://cfconventions.org/latest.html),
in conjunction with the mappings defined in the
``flattener_name_mapping_variables`` and
``flattener_name_mapping_dimensions`` global attributes, to find which
netCDF variables are *acting as* CF coordinate variables in the
flattened dataset.

For example, if an input dataset has dimension ``lat`` in the root
group and coordinate variable ``lat(lat)`` in group ``/grp1``, then
the flattened dataset will contain dimension ``lat`` and variable
``grp1__lat(lat)``, both in its root group. In this case, the
``flattener_name_mapping_variables`` global attribute of the flattened
dataset will contain the mapping ``"grp1__lat: /grp1/lat"`` and the
``flattener_name_mapping_dimensions`` global attribute will contain
the mapping ``"lat: /lat"``.


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
