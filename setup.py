"""
Py Db Report
--------

A small report system for python

"""

from setuptools import find_packages, setup

setup(
    name="pydbreport",
    version="1.0.0",
    url="https://github.com/carrerasrodrigo/pydbreport",
    license="mit",
    author="Rodrigo N. Carreras",
    author_email="carrerasrodrigo@gmail.com",
    description="A small report system for python",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms="any",
    classifiers=[],
    install_requires=[
        "jinja2>2",
        "PyMySQL>0.6",
        "SQLAlchemy",
        "croniter",
        "pytz",
        "cryptography",
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client",
    ],
    entry_points={
        "console_scripts": [
            "pydbr=pydbr.queries:main",
        ],
    },
)
