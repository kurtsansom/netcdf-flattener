# Project: NetCDF Flattener
# Copyright (c) 2020 EUMETSAT
# License: Apache License 2.0

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
