from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = 'This is a library of useful tools for Python.'
LONG_DESCRIPTION = 'This is a library of useful tools for Python.'

# Setting up
setup(
    # the name must match the folder name 'verysimplemodule'
    name="pythorn",
    version=VERSION,
    author="Officer Erik 1K-88",
    author_email="oficer.erik.k@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[], # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'

    keywords=['python', 'utils', 'tools', 'utilities'],
    classifiers= [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)