#!/usr/bin/env python
import os, re
from setuptools import setup

requirement_file = os.path.join(os.path.split(__file__)[0], "requirements.txt")
with open(requirement_file) as f:
    # Ignore comments
    requirements = [re.sub(r"#.*", "", line).replace("\n","") for line in f]

setup(
    name="tap_webcrawl",
    version="0.1",
    description="Singer.io tap for extracting data through web-crawling",
    author="Anelen Co., LLC",
    url="http://anelen.co",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_rest_api"],
    install_requires=requirements,
        entry_points="""
    [console_scripts]
    tap_webcrawl=tap_webcrawl:main
    """,
    packages=["tap_webcrawl"],
    package_data = {
    },
    include_package_data=False
)
