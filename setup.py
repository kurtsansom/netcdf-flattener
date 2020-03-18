import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='netcdf-flattener',  
     version='1.0.0',
     author="Guillaume Obrecht",
     author_email="guillaume.obrecht@c-ssystems.de",
     description="The NetCDF-flattener package",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://gitlab.eumetsat.int/additional-data-services/netcdf-flattener",
     #package_dir={'': 'netcdf_flattener'},
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
