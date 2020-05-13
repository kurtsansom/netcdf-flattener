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

from base_test import BaseTest


class Test(BaseTest):
    def test_cell_methods(self):
        """Tests the particular of the cell_methods attribute, which can contain references to dimensions, coordinate
        variables, the word "area" or any standard name.

        Flatten input file 'input4.cdl' and compare to reference 'reference4.cdl'.
        """
        # Inputs
        input_name = "input4.cdl"
        reference_name = "reference4.cdl"
        output_name = "output4.nc"

        self.flatten_and_compare(input_name, output_name, reference_name)
