# Licensed under a 3-clause BSD style license - see LICENSE.rst

# Packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from __future__ import print_function
from ._astropy_init import *
# ----------------------------------------------------------------------------

# Enforce Python version check during package import.
# This is the same check as the one at the top of setup.py
import sys

__minimum_python_version__ = "2.7"

class UnsupportedPythonError(Exception):
    pass

if sys.version_info < tuple((int(val) for val in __minimum_python_version__.split('.'))):
    raise UnsupportedPythonError("sntd does not support Python < {}".format(__minimum_python_version__))

if not _ASTROPY_SETUP_:
    # For egg_info test builds to pass, put package imports here.
    from .io import *
    from .fitting import *
    from .ml import *
    from .models import *
    from .plotting import *
    from .simulation import *
    from .spectral import *
    from .spl import *
    from .util import *
    from .version import *
    #from supcos.io import read_data,write_data
    #from supcos.fits import fit_data
    #from supcos.plots import plot_data
