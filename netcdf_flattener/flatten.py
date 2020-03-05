import hashlib
import os

from netCDF4 import Dataset


def flatten(input_file, output_file):
    Flattener(input_file).flatten(output_file)


class Flattener:

    def __init__(self, input_file):

        self.__max_name_len = 256
        self.__default_separator = '/'
        self.__new_separator = '#'
        self.__pathname_format = "{}/{}"
        self.__mapping_str_format = "{}: {}"

        self.__attr_map_name = "flattener_name_mapping_attributes"
        self.__dim_map_name = "flattener_name_mapping_dimensions"
        self.__var_map_name = "flattener_name_mapping_variables"

        self.__attr_map_value = []
        self.__dim_map_value = []
        self.__var_map_value = []

        self.__dim_map = dict()
        self.__var_map = dict()

        print("Opening input file {}".format(os.path.abspath(input_file)))
        self.__input_file = Dataset(input_file)
        self.__output_file = None

    def flatten(self, output_file):
        print("Opening output file {}".format(os.path.abspath(output_file)))
        with Dataset(output_file, 'w', format='NETCDF4') as self.__output_file:
            # Flatten product
            self.process_group(self.__input_file)

            # Add name mapping attributes
            self.__output_file.setncattr(self.__attr_map_name, self.__attr_map_value)
            self.__output_file.setncattr(self.__dim_map_name, self.__dim_map_value)
            self.__output_file.setncattr(self.__var_map_name, self.__var_map_value)

            # Browse flattened variables to rename references
            print("Browsing flattened variables to rename references in 'coordinates' attribute:")
            for var in self.__output_file.variables.values():
                self.adapt_coordinates(var)

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
        print("   Copying attribute {} from group {} to root".format(attr_name, input_group.path))

        # Create new name
        new_attr_name = self.generate_flattened_name(input_group, attr_name)

        # Write attribute
        self.__output_file.setncattr(new_attr_name, input_group.getncattr(attr_name))

        # Store new naming for later and in mapping attribute
        self.__attr_map_value.append(self.generate_mapping_str(input_group, attr_name, new_attr_name))

    def flatten_dimension(self, dim):
        print("   Copying dimension {} from group {} to root".format(dim.name, dim.group().path))

        # Create new name
        new_name = self.generate_flattened_name(dim.group(), dim.name)

        # Write dimension
        self.__output_file.createDimension(new_name, (len(dim), None)[dim.isunlimited()])

        # Store new name in dict for resolving references later
        self.__dim_map[self.pathname(dim.group(), dim.name)] = new_name

        # Add to name mapping attribute
        self.__dim_map_value.append(self.generate_mapping_str(dim.group(), dim.name, new_name))

    def flatten_variable(self, var):
        print("   Copying variable {} from group {} to root".format(var.name, var.group().path))

        # Create new name
        new_name = self.generate_flattened_name(var.group(), var.name)

        # Replace old by new dimension names
        new_dims = list(map(lambda x: self.__dim_map[self.pathname(x.group(), x.name)], var.get_dims()))

        # Write variable
        # TODO check all options
        new_var = self.__output_file.createVariable(new_name, var.dtype, new_dims, zlib=False, complevel=4,
                                                    shuffle=True, fletcher32=False, contiguous=False, chunksizes=None,
                                                    endian='native', least_significant_digit=None, fill_value=None)

        # Copy attributes
        new_var.setncatts(var.__dict__)

        # Copy data
        new_var[:] = var[:]

        # Store new name in dict for resolving references later
        self.__var_map[self.pathname(var.group(), var.name)] = new_name

        # Add to name mapping attribute
        self.__var_map_value.append(self.generate_mapping_str(var.group(), var.name, new_name))

        # Resolve coordinates and replace by absolute path
        self.resolve_coordinates(new_var, var)

    def resolve_coordinate(self, relative_coord, old_var):
        coord = relative_coord

        if coord.startswith(self.__default_separator):
            method = "absolute"
            absolute_coord = coord
        elif self.__default_separator in coord:
            method = " relative"
            parent_group = old_var.group()
            while coord.startswith("../"):
                coord = coord[3:]
                parent_group = parent_group.parent

            # TODO: handle exception if parent_group or var does not exist
            var = parent_group[coord]
            absolute_coord = self.__pathname_format.format(var.group().path, var.name)
        else:
            method = " proximity"
            resolved_var = self.search_by_proximity(coord, old_var.group(), False)
            absolute_coord = self.__pathname_format.format(resolved_var.group().path, resolved_var.name)

        print("      {} coordinate reference to '{}' resolved as '{}'".format(method, relative_coord, absolute_coord))

        return absolute_coord

    def search_by_proximity(self, coord, current_group, local_apex_reached=False):
        if coord in current_group.variables.keys():
            return current_group.variables[coord]
        elif not local_apex_reached and coord not in current_group.dimensions.keys():
            return self.search_by_proximity(coord, current_group.parent, False)
        else:
            found_var = None
            for child_group in current_group.groups.values():
                found_var = self.search_by_proximity(coord, child_group, True)
                if found_var is not None:
                    break
            return found_var

    def resolve_coordinates(self, var, old_var):
        if "coordinates" in var.__dict__:
            coord_list = var.coordinates.split()

            abs_coord_list = [self.resolve_coordinate(x, old_var) for x in coord_list]

            var.coordinates = ' '.join(abs_coord_list)

    def adapt_coordinates(self, var):
        if "coordinates" in var.__dict__:
            coord_list = var.coordinates.split()

            new_coord_list = [self.__var_map[x] for x in coord_list]

            print("   variable {}: {} renamed as {}".format(var.name, coord_list, new_coord_list))
            var.coordinates = ' '.join(new_coord_list)

    def pathname(self, group, name):
        if group.parent is None:
            return name
        else:
            return self.__pathname_format.format(group.path, name)

    def generate_mapping_str(self, input_group, name, new_name):
        original_pathname = self.pathname(input_group, name)
        mapping_str = self.__mapping_str_format.format(new_name, original_pathname)
        return mapping_str

    def convert_path_to_valid_name(self, text):
        return text.replace(self.__default_separator, '', 1).replace(self.__default_separator, self.__new_separator)

    def generate_flattened_name(self, input_group, orig_name):
        # If element is at root: no change
        if input_group.parent is None:
            new_name = orig_name

        # If element in child group, concatenate group path and element name
        else:
            full_name = self.convert_path_to_valid_name(input_group.path) + self.__new_separator + orig_name
            new_name = full_name

            # If resulting name is too long, hash group path
            if len(new_name) >= self.__max_name_len:
                group_hash = hashlib.sha1(input_group.path.encode("UTF-8")).hexdigest()
                new_name = group_hash + self.__new_separator + orig_name

                # If resulting name still too long, hash everything
                if len(new_name) >= self.__max_name_len:
                    new_name = hashlib.sha1(full_name.encode("UTF-8")).hexdigest()
        return new_name
