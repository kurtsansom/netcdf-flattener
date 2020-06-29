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

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

from netcdf_flattener import __version__

setuptools.setup(
     name='netcdf-flattener',  
     version=__version__,
     author="Guillaume Obrecht",
     author_email="guillaume.obrecht@c-ssystems.de",
     description="The NetCDF-flattener package",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://gitlab.eumetsat.int/additional-data-services/netcdf-flattener",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: Apache Software License",
         "Operating System :: OS Independent",
     ],
     install_requires=[
          'netCDF4',
      ],
 )
