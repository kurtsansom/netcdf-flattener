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
    def test_flatten(self):
        """Test of renaming rule for long names..

        Flatten input file 'input2.cdl' and compare to reference 'reference2.cdl'.
        """
        # Inputs
        input_name = "input2.cdl"
        reference_name = "reference2.cdl"
        output_name = "output2.nc"

        self.flatten_and_compare(input_name, output_name, reference_name)
