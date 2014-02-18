#!/usr/bin/env python
#
# summation_2d_integration_ext.py
#
#  Copyright (C) 2013 Diamond Light Source
#
#  Author: James Parkhurst
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.
from __future__ import division

from dials.interfaces import IntegrationIface

class Summation2dIntegrationExt(IntegrationIface):

  name = 'sum2d'

  def compute_intensity(self, reflections):
    pass

