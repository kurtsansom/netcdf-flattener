# Project: NetCDF Flattener
# Copyright (c) 2020 EUMETSAT
# License: Apache License 2.0

from test.base_test import BaseTest


class Test(BaseTest):
    def test_something(self):
        """Global test of most functionalities.

                Flatten input file 'input1.cdl' and compare to reference 'reference1.cdl'.
                """
        # Inputs
        input_name = "input3.cdl"
        reference_name = "reference3.cdl"
        output_name = "output3.nc"

        # Use strict mode, expect exception
        self.flatten_and_compare(input_name, output_name, reference_name, lax_mode=False, expect_exception=True)

        # User lax mode, expect success
        self.flatten_and_compare(input_name, output_name, reference_name, lax_mode=True, expect_exception=False)
