# setup.py  
# This file is part of gnssr_raspberry.
# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2022

import setuptools
from setuptools import find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="raspberry_gnssr",
    author="Roelof Rietbroek",
    author_email="r.rietbroek@utwente.nl",
    version="1.0",
    description="Tools to log and upload nmea messages on a raspberry-pi with GNSS pi-hat or similar on the serial port",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ITC-Water-Resources/gnssr-raspberry",
    packages=find_packages("."),
    package_dir={"":"."},
    scripts=['nmealogger.py'],
    install_requires=['pyyaml','aiohttp'],
    classifiers=["Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering",
        "Intended Audience :: Science/Research",
        "Development Status :: Beta"]
    
)
