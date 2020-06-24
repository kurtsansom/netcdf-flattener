"""Project: NetCDF Flattener
Copyright (c) 2020 EUMETSAT
License: Apache License 2.0

Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
"""

import hashlib
import os
import re
import warnings

from netCDF4 import Dataset


def flatten(input_ds, output_ds, lax_mode=False, _copy_data=True):
    """Flatten an input NetCDF dataset and write the result in an output NetCDF dataset.

    :param input_ds: input netcdf4 dataset
    :param output_ds: output netcdf4 dataset
    :param lax_mode: if false (default), not resolving a reference halts the execution. If true, continue with warning.
    :param _copy_data: if true (default), then all data arrays are copied from the input to the output dataset If false, then this does not happen. Use this option *only* if the data arrays of the flattened dataset are never to be accessed.
    """
    Flattener(input_ds, lax_mode, _copy_data=_copy_data).flatten(output_ds)


class Flattener:
    """Utility class contained the input file, the output file being flattened, and all the logic of the flattening
    process.
    """
    __max_name_len = 256
    __default_separator = '/'
    __new_separator = '#'
    __pathname_format = "{}/{}"
    __mapping_str_format = "{}: {}"
    __ref_not_found_error = "REF_NOT_FOUND"

    # attributes in which to look for references to variables, and the format of these references:
    # - 0: String attributes whose value is a blank separated list of variable names: "var1 var2
    # - 1: String attributes comprising a list of blank-separated pairs of words of the form
    #      "var1: foo var2: bar"
    # - 2: String attributes comprising a list of blank-separated pairs of words of the form
    #      "foo: var1 bar: var2"
    __var_references_attributes = {
        "ancillary_variables": 0,
        "bounds": 0,
        "cell_measures": 2,
        "climatology ": 0,
        "coordinates": 0,
        "formula_terms": 2,
        "geometry": 0,
        "grid_mapping": 0,
        "interior_ring": 0,
        "node_coordinates": 0,
        "node_count": 0,
        "nodes": 0,
        "part_node_count": 0,
    }

    # attributes in which to look for references to dimensions, and the format of these references
    __dim_references_attributes = {
        "compress": 0,
        "instance_dimension": 0,
        "sample_dimension": 0
    }

    # cell_methods attribute, which is a special case (format of the reference is 1)
    __cell_methods_attribute = "cell_methods"

    # regex expressions to read attributes
    __references_attributes_regex = {
        0: re.compile(r"(?P<var>\S+)"),
        1: re.compile(r"(?P<var>\S+): (?P<other>\S+)"),
        2: re.compile(r"(?P<other>\S+): (?P<var>\S+)")
    }

    # replacement string in attributes
    __references_attributes_replace = {
        0: "{var}{other}",  # Note: 'other' should not be used in that case
        1: "{var}: {other}",
        2: "{other}: {var}"
    }

    # name of the attributes used to store the mapping between original and flattened names
    __attr_map_name = "flattener_name_mapping_attributes"
    __dim_map_name = "flattener_name_mapping_dimensions"
    __var_map_name = "flattener_name_mapping_variables"

    def __init__(self, input_ds, lax_mode, _copy_data=True):
        """Constructor. Initializes the Flattener class given the input file.

        :param input_ds: input netcdf dataset
        :param lax_mode: if false (default), not resolving a reference halts the execution. If true, continue with warning. 
        :param _copy_data: if true (default), then all data arrays are copied from the input to the output dataset If false, then this does not happen. Use this option *only* if the data arrays of the flattened dataset are never to be accessed.
        """

        self.__attr_map_value = []
        self.__dim_map_value = []
        self.__var_map_value = []

        self.__dim_map = dict()
        self.__var_map = dict()

        self.__lax_mode = lax_mode

        self.__copy_data = _copy_data
        
        self.__input_file = input_ds
        self.__output_file = None

    def flatten(self, output_ds):
        """Flattens and write to output file

        :param output_ds: The dataset in which to store the flattened result.
        """
        # print("Opening output file {}".format(os.path.abspath(output_file)))

        if output_ds == self.__input_file \
                or output_ds.filepath() == self.__input_file.filepath() \
                or output_ds.data_model != 'NETCDF4':
            raise ValueError("Invalid inputs. Input and output datasets should be different, and output should be of "
                             "the 'NETCDF4' format.")

        self.__output_file = output_ds

        # Flatten product
        self.process_group(self.__input_file)

        # Add name mapping attributes
        self.__output_file.setncattr(self.__attr_map_name, self.__attr_map_value)
        self.__output_file.setncattr(self.__dim_map_name, self.__dim_map_value)
        self.__output_file.setncattr(self.__var_map_name, self.__var_map_value)

        # Browse flattened variables to rename references:
        # - dimensions
        print("Browsing flattened variables to rename dimension references in attributes:")
        for var in self.__output_file.variables.values():
            self.adapt_references(var, search_dim=True)

        # - variables
        print("Browsing flattened variables to rename variable references in attributes:")
        for var in self.__output_file.variables.values():
            self.adapt_references(var, search_dim=False)

        # - cell_methods
        print("Browsing flattened variables to rename references in attribute cell_methods:")
        for var in self.__output_file.variables.values():
            self.adapt_references_cell_methods(var)

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

        print(9999)
        if self.__copy_data:
            # Copy data
            new_var[:] = var[:]

        # Store new name in dict for resolving references later
        self.__var_map[self.pathname(var.group(), var.name)] = new_name

        # Add to name mapping attribute
        self.__var_map_value.append(self.generate_mapping_str(var.group(), var.name, new_name))

        # Resolve coordinates and replace by absolute path:
        # - references to dimensions
        self.resolve_references(new_var, var, search_dim=True)
        # - references to variables
        self.resolve_references(new_var, var, search_dim=False)
        # - references to dims/vars in cell_methods
        self.resolve_references_cell_methods(new_var, var)

    def resolve_reference(self, orig_ref, orig_var, search_dim, is_coordinate_variable=False):
        """Resolve the absolute path to a coordinate variable within the group structure.

        :param orig_ref: reference to resolve
        :param orig_var: variable originally containing the reference
        :param search_dim: if true, search references to dimensions, if false, search references to variables
        :param is_coordinate_variable: true, if looking for a coordinate variable
        :return: absolute path to the reference
        """
        ref = orig_ref

        # Reference is already given by absolute path
        if ref.startswith(self.__default_separator):
            method = "absolute"
            absolute_ref = ref

        # Reference is given by relative path
        elif self.__default_separator in ref:
            method = " relative"
            absolute_ref = self.search_by_relative_path(orig_ref, orig_var.group(), search_dim)
            if absolute_ref is None:
                absolute_ref = self.handle_reference_error(orig_ref, orig_var.group().path)

        # Reference is to be searched by proximity
        else:
            method = " proximity"
            resolved_var = self.search_by_proximity(ref, orig_var.group(), search_dim, False, is_coordinate_variable)
            # If not found, send warning or error
            if resolved_var is None:
                return self.handle_reference_error(ref, orig_var.group().path)
            # If found in root group
            elif resolved_var.group().parent is None:
                absolute_ref = self.__default_separator + resolved_var.name
            # If found in other group
            else:
                absolute_ref = self.__pathname_format.format(resolved_var.group().path, resolved_var.name)

        # Could resolve reference
        print("      {} coordinate reference to '{}' resolved as '{}'".format(method, orig_ref, absolute_ref))
        return absolute_ref

    def resolve_reference_cell_methods(self, orig_ref, orig_var):
        """Resolve the absolute path to a reference for the particular case of the 'cell_methods' attribute.
        This attribute is special because the reference can be to a dimension, a coordinate variable, the word 'area'
        or any standard name.

        :param orig_ref: reference to resolve
        :param orig_var: variable originally containing the reference
        :return: absolute path to the reference
        """
        if orig_ref == "area":
            print("      cell_methods: coordinate reference is key word 'area'. Skipping.")
            return orig_ref

        ref = orig_ref
        absolute_ref = None
        type = ""

        # Reference is already given by absolute path
        if ref.startswith(self.__default_separator):
            method = "absolute"
            absolute_ref = ref

        # Reference is given by relative path
        elif self.__default_separator in ref:
            method = " relative"
            # Check if is ref to var
            absolute_ref = self.search_by_relative_path(orig_ref, orig_var.group(), False)
            type = "variable "
            # Check if is ref to dim
            if absolute_ref is None:
                type = "dimension "
                absolute_ref = self.search_by_relative_path(orig_ref, orig_var.group(), True)

        # Reference is to be searched by proximity
        else:
            method = " proximity"
            # Check if is ref to var
            resolved_var = self.search_by_proximity(ref, orig_var.group(), False, False, True)
            type = "variable "
            # Check if is ref to dim
            if resolved_var is None:
                resolved_var = self.search_by_proximity(ref, orig_var.group(), True, False, False)
                type = "dimension "
            # If found
            if resolved_var is not None:
                group_name = "" if resolved_var.group().parent is None else resolved_var.group().path
                absolute_ref = self.__pathname_format.format(group_name, resolved_var.name)

        # Could not resolve reference
        if absolute_ref is None:
            print("      cell_methods: coordinate reference to '{}' in cell_methods not resolved. "
                  "Assumed to be a standard name.".format(orig_ref))
            absolute_ref = orig_ref
        # Could resolve reference
        else:
            print("      cell_methods: {} coordinate reference to '{}' resolved as {}'{}'"
                  .format(method, orig_ref, type, absolute_ref))

        return absolute_ref

    def search_by_relative_path(self, ref, current_group, search_dim):
        """Resolve the absolute path to a reference within the group structure, using search by relative path.

        :param ref: reference to resolve
        :param current_group: current group where searching
        :param search_dim: if true, search references to dimensions, if false, search references to variables
        :return: absolute path to the coordinate
        """
        # Go up parent groups
        while ref.startswith("../"):
            if current_group.parent is None:
                return None
            ref = ref[3:]
            current_group = current_group.parent

        # Go down child groups
        ref_split = ref.split(self.__default_separator)
        for g in ref_split[:-1]:
            try:
                current_group = current_group.groups[g]
            except KeyError:
                return None

        # Get variable or dimension
        elt = current_group.dimensions[ref_split[-1]] if search_dim else current_group.variables[ref_split[-1]]

        # Get absolute reference
        return self.__pathname_format.format(elt.group().path, elt.name)

    def search_by_proximity(self, ref, current_group, search_dim, local_apex_reached, is_coordinate_variable):
        """Resolve the absolute path to a reference within the group structure, using search by proximity.

        First search up in the hierarchy for the reference, until root group is reached. If coordinate variable, search
        until local apex is reached, Then search down in siblings.

        :param ref: reference to resolve
        :param current_group: current group where searching
        :param search_dim: if true, search references to dimensions, if false, search references to variables
        :param local_apex_reached: False initially, until apex is reached.
        :param is_coordinate_variable: true, if looking for a coordinate variable
        :return: absolute path to the coordinate
        """
        dims_or_vars = current_group.dimensions if search_dim else current_group.variables

        # Found in current group
        if ref in dims_or_vars.keys():
            return dims_or_vars[ref]

        local_apex_reached = local_apex_reached or ref in current_group.dimensions.keys()

        # Check if has to continue looking in parent group
        # - normal search: continue until root is reached
        # - coordinate variable: continue until local apex is reached
        if is_coordinate_variable:
            top_reached = local_apex_reached or current_group.parent is None
        else:
            top_reached = current_group.parent is None

        # Search up
        if not top_reached:
            return self.search_by_proximity(ref, current_group.parent, search_dim, local_apex_reached,
                                            is_coordinate_variable)

        # If coordinate variable and local apex reached, search down in siblings
        elif is_coordinate_variable and local_apex_reached:
            found_elt = None
            for child_group in current_group.groups.values():
                found_elt = self.search_by_proximity(ref, child_group, search_dim, local_apex_reached,
                                                     is_coordinate_variable)
                if found_elt is not None:
                    break
            return found_elt

        # If here, did not find
        else:
            return None

    def __escape_index_error(self, match, group_name):
        """Return the group in a match if it exists, an empty string otherwise.

        :param match: regex match
        :param group_name: group name
        :return: match group
        """
        try:
            return match.group(group_name)
        except IndexError:
            return ""

    def resolve_references(self, var, old_var, search_dim=False):
        """In a given variable, replace all references to other variables in its attributes by absolute references.

        :param var: flattened variable in which references should be renamed with absolute references
        :param old_var: original variable (in group structure)
        :param search_dim: if true, search references to dimensions, if false, search references to variables
        """
        if search_dim:
            attr_dict = self.__dim_references_attributes
        else:
            attr_dict = self.__var_references_attributes

        for attr_name, attr_format in attr_dict.items():
            if attr_name in var.__dict__:
                is_coordinate_variable = attr_name == "coordinates"
                regex_format = self.__references_attributes_regex[attr_format]
                replace_format = self.__references_attributes_replace[attr_format]
                attr_value = var.getncattr(attr_name)
                new_attr_value = regex_format.sub(lambda x: replace_format.format(
                    var=self.resolve_reference(x.group("var"), old_var, search_dim, is_coordinate_variable),
                    other=self.__escape_index_error(x, "other")), attr_value)
                var.setncattr(attr_name, new_attr_value)

    def resolve_references_cell_methods(self, var, old_var):
        """In a given variable, replace all references inside the 'cell_methods' attribute by absolute references.

        :param var: flattened variable in which references should be renamed with absolute references
        :param old_var: original variable (in group structure)
        """
        if self.__cell_methods_attribute in var.__dict__:
            regex_format = self.__references_attributes_regex[1]
            replace_format = self.__references_attributes_replace[1]
            attr_value = var.getncattr(self.__cell_methods_attribute)
            new_attr_value = regex_format.sub(lambda x: replace_format.format(
                var=self.resolve_reference_cell_methods(x.group("var"), old_var),
                other=self.__escape_index_error(x, "other")), attr_value)
            var.setncattr(self.__cell_methods_attribute, new_attr_value)

    def adapt_references(self, var, search_dim=False):
        """In a given variable, replace all references to variables in attributes by references to the new names in the
        flattened NetCDF. All references have to be already resolved as absolute references.

        :param var: flattened variable in which references should be renamed with new names
        :param search_dim: if true, search references to dimensions, if false, search references to variables
        """
        if search_dim:
            attr_dict = self.__dim_references_attributes
            name_mapping = self.__dim_map
        else:
            attr_dict = self.__var_references_attributes
            name_mapping = self.__var_map

        for attr_name, attr_format in attr_dict.items():
            if attr_name in var.__dict__:
                attr_value = var.getncattr(attr_name)
                regex_format = self.__references_attributes_regex[attr_format]
                replace_format = self.__references_attributes_replace[attr_format]
                new_attr_value = regex_format.sub(lambda x: replace_format.format(
                    var=self.adapt_name(name_mapping, x.group("var")),
                    other=self.__escape_index_error(x, "other")), attr_value)
                var.setncattr(attr_name, new_attr_value)
                print("   attribute '{}'  in {} '{}': references '{}' renamed as '{}'"
                      .format(attr_name, ("variable", "dimension")[search_dim], var.name, attr_value, new_attr_value))

    def adapt_references_cell_methods(self, var):
        """In a given variable, replace all references in cell_methods attributes by references to the new names in the
        flattened NetCDF. All references have to be already resolved as absolute references.

        :param var: flattened variable in which references should be renamed with new names
        """
        if self.__cell_methods_attribute in var.__dict__:
            regex_format = self.__references_attributes_regex[1]
            replace_format = self.__references_attributes_replace[1]
            attr_value = var.getncattr(self.__cell_methods_attribute)
            new_attr_value = regex_format.sub(lambda x: replace_format.format(
                var=self.adapt_name_cell_methods(x.group("var")),
                other=self.__escape_index_error(x, "other")), attr_value)
            var.setncattr(self.__cell_methods_attribute, new_attr_value)
            print("   attribute 'cell_method'  in '{}': references '{}' renamed as '{}'"
                  .format(var.name, attr_value, new_attr_value))

    def adapt_name(self, name_mapping, resolved_ref):
        """Return name of flattened reference. If not found, raise exception or continue warning.

        :param name_mapping: dictionary containing name mapping
        :param resolved_ref: resolved reference to adapt
        :return: adapted reference
        """
        try:
            # If could reference could not be resolved, leave error message as reference
            if self.__ref_not_found_error in resolved_ref:
                return resolved_ref
            # Else, replace by new name
            else:
                return name_mapping[resolved_ref]

        # If not found in mapping, warning or exception
        except KeyError:
            return self.handle_reference_error(resolved_ref)

    def adapt_name_cell_methods(self, resolved_ref):
        """Return name of flattened reference. First look for name as variable, then as dimension. If not found, leave
        as it is.

        :param resolved_ref: resolved reference to adapt
        :return: adapted reference
        """
        if resolved_ref in self.__var_map:
            return self.__var_map[resolved_ref]
        elif resolved_ref in self.__dim_map:
            return self.__dim_map[resolved_ref]
        else:
            return resolved_ref

    def pathname(self, group, name):
        """Compose full path name to an element in a group structure: /path/to/group/elt

        :param group: group containing element
        :param name: name of the element
        :return: pathname
        """
        if group.parent is None:
            return self.__default_separator + name
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

    def handle_reference_error(self, ref, context=None):
        """Depending on lax/strict mode, either raise exception or log warning. If lax, return reference placeholder.

        :param ref: reference
        :param context: additional context info to add to message
        :return: if continue with warning, error replacement name for reference
        """
        message = "Reference '{}' could not be resolved".format(ref)
        if context is not None:
            message = message + " from {}".format(context)
        if self.__lax_mode:
            warnings.warn(message)
            return self.__ref_not_found_error + ":_" + ref
        else:
            raise ReferenceException(message)


class ReferenceException(Exception):
    """Exception raised when references in attributes cannot be resolved.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        super().__init__(message)
