Getting started
===============

The aim of this tutorial is to provide a quick start guide to running DIALS for
integrating good quality synchrotron X-ray diffraction data. Please note that
DIALS only does data processing you will need to use e.g. Aimless for the
subsequent scaling.

Introduction
------------

The philosophy behind DIALS is to be explicit in performing the various steps of
data analysis rather than giving one big tool - DIALS is first and foremost a
toolkit for doing the data analysis to be used within other systems.

One such system is `xia2 <http://xia2.sourceforge.net/>`_, which is included
in the DIALS installers, and supports processing with DIALS, in addition to XDS
and MOSFLM. To use DIALS within xia2, simply use the ``-dials`` flag::

  xia2 -dials /path/to/image/

For more information on using xia2 see the
`xia2 documentation <http://xia2.sourceforge.net/>`_. The rest of this tutorial
will concentrate on running the individual DIALS command line programs directly.


Import
------

There are three ways of importing images ::

  dials.import /path/to/the/data/*.img

or ::

  dials.import /path/to/the/data/template_####.img

where ``####`` represents the image number that increments from image to image,
or ::

  find /path/to/the/data -name *.img | dials.import -i

The latter of these is useful when you have a limited number of command-line
options. This creates datablock.json which is a DIALS description of this data
set.

Find Spots
----------

Most useful parameter here is the minimum spots size. By default it is 3 for
pixel array detectors (e.g. Pilatus detectors), and 6 otherwise
(e.g. CCD detectors), but this can be overridden with min_spot_size=N where N
is e.g. 3. This takes datablock.json and creates strong.pickle::

  dials.find_spots min_spot_size=3 datablock.json

(for example)

Index
-----

The indexing for DIALS offers a substantial number of options - these are
detailed in the Phil file for dials.index, which is shown when you run the
program. The most useful options are::

  unit_cell=a,b,c,al,be,ga
  space_group=P4 (say)
  indexing.method=fft3d (say)

The indexing works as ::

  dials.index strong.pickle datablock.json [options]

and creates an "experiment" file experiment.json which details the crystal
lattices found and indexed.pickle, which is a copy of strong.pickle with Miller
indices and reflection predictions added.

If you are unsure of the symmetry and would like to know how different lattices
look in the refinement, run dials.index not specifying the symmetry and then run
dials.refine_bravais_settings.

Refinement
----------

The indexing includes refinement - if you do not wish to use a scan-varying
crystal model you can go straight to integration. If you do want to use a time
varying model, you will need to rerun the refinement with this new model as ::

  dials.refine experiments.json indexed.pickle scan_varying=true

which will generate refined_experiments.json - this you pass on to integration.

Integration
-----------

As may be expected the integration in DIALS offers the greatest range of user
options, to control how the background is determined (including outlier pixels
in the background determination) the reflection profile parameters (used to
define the reflection mask, and by default discovered automatically) and the
actual algorithm to be used for peak integration::

  dials.integrate outlier.algorithm=null refined_experiments.json indexed.pickle

This reads the indexed reflections to determine strong reflections for profile
fitting and integrates the data in refined_experiments.json, using the default
background determination with no outlier rejection and XDS-style 3D profile
fitting.

Export
------

If you have got this far everything else is easy: export the data as MTZ then
run pointless_ and aimless_ to re-sort and scale the data::

  dials.export_mtz integrated.pickle refined_experiments.json
  pointless hklin integrated.mtz hklout sorted.mtz
  aimless hklin sorted.mtz hklout scaled.mtz

For details on pointless_ and aimless_ please refer to the CCP4 documentation.


.. rubric:: Footnotes

.. [#f1] Currently necessary for data in HDF5 files

.. _pointless: http://www.ccp4.ac.uk/html/pointless.html
.. _aimless: http://www.ccp4.ac.uk/html/aimless.html
