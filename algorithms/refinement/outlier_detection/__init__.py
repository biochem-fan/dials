#!/usr/bin/env python
#
#  __init__.py
#
#  Copyright (C) 2015 Diamond Light Source and STFC Rutherford Appleton
#                     Laboratory, UK.
#
#  Author: David Waterman
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.

from __future__ import division
from outlier_base import CentroidOutlier, CentroidOutlierFactory
from outlier_base import phil_str, phil_scope
from mcd import MCD
from tukey import Tukey
