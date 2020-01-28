from netCDF4 import Dataset


def flatten(input_file, output_file):
    print("Opening input file {}".format(input_file))
    input_ds = Dataset(input_file)

    print("Opening output file {}".format(output_file))
    with Dataset(output_file, 'w', format='NETCDF4') as file:
        # for var in inputds.variables.keys():
        #     print(input_ds.variables.get(var))
        #     file.variables[var] = input_ds.variables.get(var)

        for attr_name in input_ds.ncattrs():
            print("Copying attribute: {}: {}".format(attr_name, input_ds.getncattr(attr_name)))
            file.setncattr(attr_name, input_ds.getncattr(attr_name))

