#!/usr/bin/env python
#
# dials.filter_reflections.py
#
#  Copyright (C) 2015 STFC Rutherford Appleton Laboratory, UK.
#
#  Author: David Waterman
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.

from __future__ import division

help_message = '''

This program takes reflection files as input and filters them based on user-
specified criteria, to write out a subset of the original file.

Example::

  dials.filter_reflections refined.pickle include.flag=used_in_refinement'''

class Script(object):
  '''A class for running the script.'''

  def __init__(self):
    '''Initialise the script.'''
    from dials.util.options import OptionParser
    from libtbx.phil import parse
    import libtbx.load_env

    phil_scope = parse('''

      output {
        reflections = 'filtered.pickle'
          .type = str
          .help = "The filtered reflections output filename"
      }

      inclusions {
        flag = integrated_prf overloaded integrated_sum centroid_outlier bad_spot dont_integrate reference_spot overlapped_bg observed used_in_refinement used_in_modelling predicted in_powder_ring bad_shoebox indexed strong integrated overlapped_fg
          .type = choice
          .help = "Include reflections with this flag to form the working set."
          .multiple = True
      }

      exclusions {
        flag = integrated_prf overloaded integrated_sum centroid_outlier bad_spot dont_integrate reference_spot overlapped_bg observed used_in_refinement used_in_modelling predicted in_powder_ring bad_shoebox indexed strong integrated overlapped_fg
          .type = choice
          .help = "Exclude reflections from the working set with this flag."
          .multiple = True
      }

    ''')

    # The script usage
    usage  = "usage: %s [options] experiment.json" % libtbx.env.dispatcher_name

    # Create the parser
    self.parser = OptionParser(
      usage=usage,
      phil=phil_scope,
      epilog=help_message,
      read_reflections=True)

  def run(self):
    '''Execute the script.'''
    from dials.array_family import flex
    from dials.util.options import flatten_reflections
    from libtbx.utils import Sorry

    # Parse the command line
    params, options = self.parser.parse_args(show_diff_phil=True)
    reflections = flatten_reflections(params.input.reflections)
    if len(reflections) == 0:
      raise Sorry('No valid reflection file given')
    if len(reflections) != 1:
      raise Sorry('Exactly 1 reflection file must be specified')
    reflections = reflections[0]

    print "{0} reflections loaded".format(len(reflections))

    if len(params.inclusions.flag) == 0:
      raise Sorry('No inclusion criteria given')

    # Build up the initial inclusion selection
    inc = flex.bool(len(reflections))
    for flag in params.inclusions.flag:
      sel = reflections.get_flags(getattr(reflections.flags, flag))
      inc = inc | sel
    reflections = reflections.select(inc)

    print "{0} reflections selected to form the working set".format(len(reflections))

    # Make requested exclusions from the current selection
    exc = flex.bool(len(reflections))
    for flag in params.exclusions.flag:
      print flag
      sel = reflections.get_flags(getattr(reflections.flags, flag))
      exc = exc | sel
    reflections = reflections.select(~exc)

    print "{0} reflections excluded from the working set".format(exc.count(True))

    # Save filtered reflections to file
    if params.output.reflections:
      print "Saving {0} reflections to {1}".format(len(reflections),
                                                   params.output.reflections)
      reflections.as_pickle(params.output.reflections)

    return

if __name__ == '__main__':
  from dials.util import halraiser
  try:
    script = Script()
    script.run()
  except Exception as e:
    halraiser(e)
