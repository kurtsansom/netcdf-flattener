import os

from netCDF4 import Dataset


def flatten(input_file, output_file):
    Flattener(input_file).flatten(output_file)


def pathname(group, name):
    if group.parent is None:
        return name
    else:
        return "{}/{}".format(group.path, name)


def convert_path_to_valid_name(text):
    return text.replace('/', '', 1).replace('/', '#')


def generate_flattened_name(input_group, orig_name):
    # TODO: hash if name too long
    if input_group.parent is None:
        new_name = orig_name
    else:
        new_name = convert_path_to_valid_name(input_group.path) + "#" + orig_name
    return new_name


def generate_mapping_str(input_group, name, new_name):
    original_pathname = pathname(input_group, name)
    mapping_str = "{}: {}".format(new_name, original_pathname)
    return mapping_str


class Flattener:

    def __init__(self, input_file):

        self.__mapping_attr = "flattener_name_mapping_attributes"
        self.__mapping_dim = "flattener_name_mapping_dimensions"
        self.__mapping_var = "flattener_name_mapping_variables"

        self.__dim_map = dict()

        print("Opening input file {}".format(os.path.abspath(input_file)))
        self.__input_file = Dataset(input_file)
        self.__output_file = None;

    def flatten(self, output_file):
        print("Opening output file {}".format(os.path.abspath(output_file)))
        with Dataset(output_file, 'w', format='NETCDF4') as self.__output_file:
            self.process_group(self.__input_file)

    def process_group(self, input_group):
        print("Browsing group " + input_group.path)
        for attr_name in input_group.ncattrs():
            self.flatten_attribute(input_group, attr_name)

        for dim in input_group.dimensions.values():
            self.flatten_dimension(dim)

        for var in input_group.variables.values():
            self.flatten_variable(var)

        for child_group in input_group.groups.values():
            self.process_group(child_group)

    def flatten_attribute(self, input_group, attr_name):
        print("Copying attribute {} from group {} to root".format(attr_name, input_group.path))

        # Create new name
        new_attr_name = generate_flattened_name(input_group, attr_name)

        # Write attribute
        self.__output_file.setncattr(new_attr_name, input_group.getncattr(attr_name))

        # Add to name mapping
        mapping_str = generate_mapping_str(input_group, attr_name, new_attr_name)
        try:
            mapping = self.__output_file.getncattr(self.__mapping_attr)
        except AttributeError:
            mapping = [mapping_str]
        mapping.append(mapping_str)
        self.__output_file.setncattr(self.__mapping_attr, mapping)

    def flatten_dimension(self, dim):
        print("Copying dimension {} from group {} to root".format(dim.name, dim.group().path))

        # Create new name
        new_name = generate_flattened_name(dim.group(), dim.name)

        # Write dimension
        self.__output_file.createDimension(new_name, (len(dim), None)[dim.isunlimited()])

        # Store new dimension name for later
        self.__dim_map[pathname(dim.group(), dim.name)] = new_name

        # Add to name mapping
        mapping_str = generate_mapping_str(dim.group(), dim.name, new_name)
        try:
            mapping = self.__output_file.getncattr(self.__mapping_dim)
        except AttributeError:
            mapping = [mapping_str]
        mapping.append(mapping_str)
        self.__output_file.setncattr(self.__mapping_dim, mapping)

    def flatten_variable(self, var):
        print("Copying variable {} from group {} to root".format(var.name, var.group().path))

        # Create new name
        new_name = generate_flattened_name(var.group(), var.name)

        # Match old/new dimension names
        new_dims = list(map(lambda x: self.__dim_map[pathname(x.group(), x.name)], var.get_dims()))

        # Write variable
        # TODO check all options
        new_var = self.__output_file.createVariable(new_name, var.dtype, new_dims, zlib=False, complevel=4, shuffle=True, fletcher32=False, contiguous=False, chunksizes=None, endian='native', least_significant_digit=None, fill_value=None)

        # Copy attributes
        new_var.setncatts(var.__dict__)

        # TODO: deal with "coordinates" attribute
#
# print("Main")
# flatten("../../cf_grp.nc", "../../cf_flat.nc")
