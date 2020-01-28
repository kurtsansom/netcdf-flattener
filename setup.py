import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='netcdf-flattener',  
     version='0.0.1',
#     scripts=['src/test'] ,
     author="Guillaume Obrecht",
     author_email="guillaume.obrecht@c-ssystems.de",
     description="The NetCDF-flattener package",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://gitlab.eumetsat.int/additional-data-services/netcdf-flattener",
     package_dir={'': 'netcdf_flattener'},
     packages=setuptools.find_packages('netcdf_flattener'),
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: Apache Software License",
         "Operating System :: OS Independent",
     ],
 )
