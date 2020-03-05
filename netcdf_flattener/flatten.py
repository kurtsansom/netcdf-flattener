# Project: NetCDF Flattener
# Copyright (c) 2020 EUMETSAT
# License: Proprietary

import hashlib
import os

from netCDF4 import Dataset


def flatten(input_file, output_file):
    """Flatten an input NetCDF file and write the result in an output NetCDF file.

    :param input_file: input file name
    :param output_file: output file name
    """
    Flattener(input_file).flatten(output_file)


class Flattener:

    def __init__(self, input_file):
        """Constructor. Initializes the Flattener class given the input file.

        :param input_file: input file name
        """
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
        """Flattens and write to output file

        :param output_file:
        """
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
                self.adapt_coordinates_names(var)

    def process_group(self, input_group):
        """Flattens a given group to the output file.

        :param input_group: group to flatten
        """
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
        """Flattens a given attribute from a group to the output file.

        :param input_group: group containing the attribute to flatten
        :param attr_name: name of the attribute to flatten
        """
        print("   Copying attribute {} from group {} to root".format(attr_name, input_group.path))

        # Create new name
        new_attr_name = self.generate_flattened_name(input_group, attr_name)

        # Write attribute
        self.__output_file.setncattr(new_attr_name, input_group.getncattr(attr_name))

        # Store new naming for later and in mapping attribute
        self.__attr_map_value.append(self.generate_mapping_str(input_group, attr_name, new_attr_name))

    def flatten_dimension(self, dim):
        """Flattens a given dimension to the output file.

        :param dim: dimension to flatten
        """
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
        """Flattens a given variable to the output file.

        :param var: variable to flatten
        """
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

    def resolve_coordinate(self, orig_coord, orig_var):
        """Resolve the absolute path to a coordinate variable within the group structure.

        :param orig_coord: coordinate to resolve
        :param orig_var: variable originally containing the coordinate reference
        :return: absolute path to the coordinate
        """
        coord = orig_coord

        # Coordinate is already given by absolute path
        if coord.startswith(self.__default_separator):
            method = "absolute"
            absolute_coord = coord

        # Coordinate is given by relative path
        elif self.__default_separator in coord:
            method = " relative"
            parent_group = orig_var.group()
            while coord.startswith("../"):
                coord = coord[3:]
                parent_group = parent_group.parent

            # TODO: handle exception if parent_group or var does not exist
            var = parent_group[coord]
            absolute_coord = self.__pathname_format.format(var.group().path, var.name)

        # Coordinate is to be searched by proximity
        else:
            method = " proximity"
            resolved_var = self.search_by_proximity(coord, orig_var.group(), False)
            absolute_coord = self.__pathname_format.format(resolved_var.group().path, resolved_var.name)

        print("      {} coordinate reference to '{}' resolved as '{}'".format(method, orig_coord, absolute_coord))
        return absolute_coord

    def search_by_proximity(self, coord, current_group, local_apex_reached=False):
        """Resolve the absolute path to a coordinate variable within the group structure, using search by proximity.

        First search up in the hierarchy for the coordinate, until local apex is reached. Then search down in siblings.

        :param coord: coordinate to resolve
        :param current_group: current group where searching
        :param local_apex_reached: False initially, until apex is reached.
        :return: absolute path to the coordinate
        """
        # Found in current group
        if coord in current_group.variables.keys():
            return current_group.variables[coord]

        # If local apex not reached, search in parent group
        elif not local_apex_reached and coord not in current_group.dimensions.keys():
            return self.search_by_proximity(coord, current_group.parent, False)

        # If local apex reached, search down in siblings
        else:
            found_var = None
            for child_group in current_group.groups.values():
                found_var = self.search_by_proximity(coord, child_group, True)
                if found_var is not None:
                    break
            return found_var

    def resolve_coordinates(self, var, old_var):
        """In a given variable, replace all references to coordinates by absolute references.

        :param var: flattened variable in which coordinates should be renamed with absolute references
        :param old_var: original variable (in group structure)
        """
        if "coordinates" in var.__dict__:
            coord_list = var.coordinates.split()

            abs_coord_list = [self.resolve_coordinate(x, old_var) for x in coord_list]

            var.coordinates = ' '.join(abs_coord_list)

    def adapt_coordinates_names(self, var):
        """In a given variable, replace all references to coordinates by references to the new names in the flattened
        NetCDF. All references have to be absolute references to be found.

        :param var: flattened variable in which coordinates should be renamed with new names
        """
        if "coordinates" in var.__dict__:
            coord_list = var.coordinates.split()

            new_coord_list = [self.__var_map[x] for x in coord_list]

            print("   variable {}: {} renamed as {}".format(var.name, coord_list, new_coord_list))
            var.coordinates = ' '.join(new_coord_list)

    def pathname(self, group, name):
        """Compose full path name to an element in a group structure: /path/to/group/elt

        :param group: group containing element
        :param name: name of the element
        :return: pathname
        """
        if group.parent is None:
            return name
        else:
            return self.__pathname_format.format(group.path, name)

    def generate_mapping_str(self, input_group, name, new_name):
        """Generate a string representing the name mapping of an element before and after flattening.

        :param input_group: group containing the non-flattened element
        :param name: name of the non-flattened element
        :param new_name: name of the flattened element
        :return: string representing the name mapping for the element
        """
        original_pathname = self.pathname(input_group, name)
        mapping_str = self.__mapping_str_format.format(new_name, original_pathname)
        return mapping_str

    def convert_path_to_valid_name(self, pathname):
        """Generate valid name from path.

        :param pathname: pathname
        :return: valid NetCDF name
        """
        return pathname.replace(self.__default_separator, '', 1).replace(self.__default_separator, self.__new_separator)

    def generate_flattened_name(self, input_group, orig_name):
        """Convert full path of an element to a valid NetCDF name:
            - the name of an element is the concatenation of its containing group and its name,
            - replaces / from paths (forbidden as NetCDF name),
            - if name is longer than 255 characters, replace path to group by hash,
            - if name is still too long, replace complete name by hash.

        :param input_group: group containing element
        :param orig_name: original name of the element
        :return: new valid name of the element
        """
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
