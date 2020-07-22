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

"""Base test module to inherit from actual tests.
"""
import os
import re
import sys
import subprocess
from pathlib import Path
from unittest import TestCase
from netCDF4 import Dataset

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netcdf_flattener import flatten
from netcdf_flattener import ReferenceException


def make_string_comparable(text):
    """Clean CDl formatting to allow diff

    :param text: test to clean
    :return: cleaned text
    """
    text = re.sub('\n[\t ]+', '\n', text)
    text = re.sub('[\t ]+', ' ', text)
    text = re.sub('\n]+', '\n', text)
    text = re.sub(r':_NCProperties = "[\w+.=,]*" *;\n', '', text)
    return text


class BaseTest(TestCase):
    """Base test class

    This class contains regular functions that can be used to create tests.

    Attributes:
        test_data_folder:   path to the test data folder
    """

    test_data_folder = "data"

    def flatten_and_compare(self, input_name, output_name, reference_name, lax_mode=False, expect_exception=False,
                            copy_slices=None):
        """From input CDL, generate a NetCDF file, flatten it and compare its content to a reference CDL

        :param input_name: pathname to input CDL file
        :param output_name: name to use for flattened NetCDF
        :param reference_name: reference CDL to use to validate flattened CDL
        :param lax_mode: false (default) for halting when reference not resolved, true for warnings
        :param expect_exception: if true, excepts the flattener to raise a ReferenceException
        :param copy_slices: "copy_slices" argument to pass on to API
        """
        # Compose full file names
        test_data_path = Path(Path(__file__)).parent / self.test_data_folder
        input_cdl = test_data_path / input_name
        input_nc = test_data_path / "{}.nc".format(input_name)
        output_nc = test_data_path / output_name
        reference_cdl = test_data_path / reference_name

        # Generate NetCDF from input CDL
        print("Generate NetCDF file '{}' from input CDL '{}'".format(input_nc, input_cdl))
        subprocess.call(["ncgen", "-o", input_nc, input_cdl])  # nosec

        # Run flattening script
        print("Flatten '{}' in new file '{}'".format(input_nc, output_nc))

        # Run flattener and expect to a Reference Exception
        if expect_exception:
            with self.assertRaises(ReferenceException) as context:
                input_ds = Dataset(input_nc)
                output_ds = Dataset(output_nc, 'w', format='NETCDF4')
                flatten(input_ds, output_ds, lax_mode=lax_mode, copy_slices=copy_slices)
            print("Got exception as expected: {}". format(context.exception))
            input_ds.close()
            output_ds.close()
            os.remove(input_nc)
            assert True
        # Expect flattener to succeed
        else:
            input_ds = Dataset(input_nc)
            output_ds = Dataset(output_nc, 'w', format='NETCDF4')
            flatten(input_ds, output_ds, lax_mode=lax_mode, copy_slices=copy_slices)
            input_ds.close()
            output_ds.close()

            # Dump flattened NetCDF and compare to reference
            print("Read content of flattened netcdf file '{}' in CDL (ncdump)".format(output_nc))
            dumped_text = subprocess.check_output(["ncdump", output_nc]).decode("utf-8")  # nosec

            print("Read content of reference CDL file '{}'".format(reference_cdl))
            with open(reference_cdl, 'r') as content_file:
                reference_dump = content_file.read()

            str1 = make_string_comparable(dumped_text)
            str2 = make_string_comparable(reference_dump)

            # Clean created files
            os.remove(input_nc)
            os.remove(output_nc)

            # Compare flattened to reference
            test_result = str1 == str2

            if not test_result:
                print("Strings don't match!\n\nReference:\n")
                print(str2)
                print("\n\nGenerated:\n")
                print(str1)
            else:
                print("Strings match")
                
            assert test_result
