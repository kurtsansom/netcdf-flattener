# Project: NetCDF Flattener
# Copyright (c) 2020 EUMETSAT
# License: Apache License 2.0

from base_test import BaseTest


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
