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

import subprocess
from pathlib import Path
from netCDF4 import Dataset

from netcdf_flattener import flatten

from base_test import BaseTest


def walktree(top):
    values = top.groups.values()
    yield values
    for value in top.groups.values():
        for children in walktree(value):
            yield children

def assert_expected_data(self, _copy_data, variable_in, variable_out):
    if _copy_data:
        self.assertEqual(variable_in.shape, variable_out.shape)
        self.assertTrue(
            (variable_in[...].data == variable_out[...].data).all()
        )
    else:
        if variable_in.shape == variable_out.shape:
            self.assertFalse(
                (variable_in[...].data == variable_out[...].data).all()
            )

class Test(BaseTest):
    def test_flatten(self):
        """Global test of most functionalities.

        Flatten input file 'input1.cdl' and compare to reference 'reference1.cdl'.
        """
        # Inputs
        input_name = "input1.cdl"
        reference_name = "reference1.cdl"
        output_name = "output1.nc"

        self.flatten_and_compare(input_name, output_name, reference_name)

    def test_flatten_copy_data(self):
        """Test of _copy_data functionality.

        Flatten input file 'input1.cdl' with _copy_data True/False,
        checking that the data is copied/not copied.

        """
        input_name = "input1.cdl"
        output_name = "output1.nc"

        # Compose full file names
        test_data_path = Path(Path(__file__)).parent / self.test_data_folder
        input_cdl = test_data_path / input_name
        input_nc = test_data_path / "{}.nc".format(input_name)
        output_nc = test_data_path / output_name

        # Generate NetCDF from input CDL
        print("Generate NetCDF file '{}' from input CDL '{}'".format(input_nc, input_cdl))
        subprocess.call(["ncgen", "-o", input_nc, input_cdl])

        # Run flattening script
        print("Flatten '{}' in new file '{}'".format(input_nc, output_nc))

        input_ds = Dataset(input_nc, 'r')

        # Run flattener with _copy_data True/False
        for _copy_data in (True, False):        
            output_ds = Dataset(output_nc, 'w', format='NETCDF4')
            flatten(input_ds, output_ds, _copy_data=_copy_data)
    
            for key, variable_in in input_ds.variables.items():
                variable_out = output_ds.variables[key]
                assert_expected_data(self, _copy_data, variable_in,
                                     variable_out)
                    
            for children in walktree(input_ds):
                for child in children:
                    for key, variable_in in child.variables.items():
                        path = variable_in.group().path
                        flat_key = '__'.join(path.split('/')[1:] + [key])
                        variable_out = output_ds.variables[flat_key]
                        assert_expected_data(self, _copy_data,
                                             variable_in, variable_out)
                        
            output_ds.close()

        input_ds.close()
