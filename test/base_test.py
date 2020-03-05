"""Base test module to inherit from actual tests.
"""
import os
import re
import subprocess
from pathlib import Path
from unittest import TestCase

from netcdf_flattener import flatten


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

    def flatten_and_compare(self, input_name, output_name, reference_name):
        """From input CDL, generate a NetCDF file, flatten it and compare its content to a reference CDL

        :param input_name: pathname to input CDL file
        :param output_name: name to use for flattened NetCDF
        :param reference_name: reference CDL to use to validate flattened CDL
        """
        # Compose full file names
        test_data_path = Path(Path(__file__)).parent / self.test_data_folder
        input_cdl = test_data_path / input_name
        input_nc = test_data_path / "{}.nc".format(input_name)
        output_nc = test_data_path / output_name
        reference_cdl = test_data_path / reference_name

        # Generate NetCDF from input CDL
        print("Generate NetCDF file '{}' from input CDL '{}'".format(input_nc, input_cdl))
        subprocess.call(["ncgen", "-o", input_nc, input_cdl])

        # Run flattening script
        print("Flatten '{}' in new file '{}'".format(input_nc, output_nc))
        flatten(input_nc, output_nc)

        # Dump flattened NetCDF and compare to reference
        print("Read content of flattened netcdf file '{}' in CDL (ncdump)".format(output_nc))
        dumped_text = subprocess.check_output(["ncdump", output_nc]).decode("utf-8")

        print("Read content of reference CDL file '{}'".format(reference_cdl))
        with open(reference_cdl, 'r') as content_file:
            reference_dump = content_file.read()

        str1 = make_string_comparable(dumped_text)
        str2 = make_string_comparable(reference_dump)

        # Clean created files
        os.remove(input_nc)
        os.remove(output_nc)

        # Test
        test_result = str1 == str2

        if not test_result:
            print("Strings don't match!\n\nReference:\n")
            print(str2)
            print("\n\nGenerated:\n")
            print(str1)
        else:
            print("Strings match")

        assert test_result
