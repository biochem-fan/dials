#!/usr/bin/env dials.python
from __future__ import division
from libtbx.phil import parse

"""Utility script to split experiments and reflections from single files into
multiple files with one experiment per output experiment file and one
reflection file per output experiment file.
"""

class Script(object):

  def __init__(self):
    '''Initialise the script.'''
    from dials.util.options import OptionParser
    from libtbx.phil import parse
    import libtbx.load_env

    # The phil scope
    phil_scope = parse('''

      output {
        experiments_prefix = experiments
          .type = str
          .help = "Filename prefix for the split experimental models"

        reflections_prefix = reflections
          .type = str
          .help = "Filename prefix for the split reflections"
      }
    ''', process_includes=True)

    # The script usage
    usage  = "usage: %s [options] [param.phil] " \
             "experiments1.json experiments2.json reflections1.pickle " \
             "reflections2.pickle..." \
             % libtbx.env.dispatcher_name

    # Create the parser
    self.parser = OptionParser(
      usage=usage,
      phil=phil_scope,
      read_reflections=True,
      read_experiments=True,
      check_format=False)

  def run(self):
    '''Execute the script.'''

    from dials.util.options import flatten_reflections, flatten_experiments
    from libtbx.utils import Sorry
    from dials.array_family import flex

    # Parse the command line
    params, options = self.parser.parse_args(show_diff_phil=True)

    # Try to load the models and data
    if len(params.input.experiments) == 0:
      print "No Experiments found in the input"
      self.parser.print_help()
      return
    if len(params.input.reflections) == 0:
      print "No reflection data found in the input"
      self.parser.print_help()
      return
    try:
      assert len(params.input.reflections) == len(params.input.experiments)
    except AssertionError:
      raise Sorry("The number of input reflections files does not match the "
        "number of input experiments")

    experiments = flatten_experiments(params.input.experiments)
    reflections = flatten_reflections(params.input.reflections)[0]

    import math
    experiments_template = "%s_%%0%sd.json" %(
      params.output.experiments_prefix,
      int(math.floor(math.log10(len(experiments))) + 1))
    reflections_template = "%s_%%0%sd.pickle" %(
      params.output.reflections_prefix,
      int(math.floor(math.log10(len(experiments))) + 1))

    for i, experiment in enumerate(experiments):
      ref_sel = reflections.select(reflections['id'] == i)
      ref_sel['id'] = flex.int(len(ref_sel), 0)

      from dxtbx.model.experiment.experiment_list import ExperimentList
      from dxtbx.serialize import dump
      experiment_filename = experiments_template %i
      reflections_filename = reflections_template %i
      print 'Saving experiment %d to %s' %(i, experiment_filename)
      dump.experiment_list(ExperimentList([experiment]), experiment_filename)
      print 'Saving reflections for experiment %d to %s' %(i, reflections_filename)
      ref_sel.as_pickle(reflections_filename)

    return

if __name__ == "__main__":
  from dials.util import halraiser
  try:
    script = Script()
    script.run()
  except Exception as e:
    halraiser(e)

