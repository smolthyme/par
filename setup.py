__doc__ = """
=====================
Par 
=====================

:Author: Limodou <limodou@gmail.com>

About Par
----------------

Par is a simple structured text parser project. It based on pyPEG (req. version included) for now. 

It supports and extends markdown syntax, as well as some other small 'languages'.

License
------------

Par is released under BSD license."""

from setuptools import setup

setup(name='par',
    version='1.4.0',
    description="A simple structured text parser",
    long_description=__doc__,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.12",
    ],
    packages = ['par'],
    platforms = 'any',
    keywords='parser peg',
    author='limodou',
    author_email='limodou@gmail.com',
    url='https://github.com/limodou/par',
    license='BSD',
    include_package_data=True,
    zip_safe=False,
)
