#
# factory.py
#
#  Copyright (C) 2013 Diamond Light Source
#
#  Author: James Parkhurst
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.

from __future__ import division

class Factory(object):
  ''' A factory class to compute the profile models. '''

  @classmethod
  def compute_single(cls, experiment, reflections, min_zeta=0.05):
    ''' Compute the profile model. '''
    from dials.algorithms.profile_model.gaussian_rs.calculator \
      import ProfileModelCalculator
    from dials.algorithms.profile_model.gaussian_rs import ProfileModel
    calculator = ProfileModelCalculator(experiment, reflections, min_zeta)
    n_sigma = 3
    sigma_b = calculator.sigma_b()
    sigma_m = calculator.sigma_m()
    return ProfileModel(n_sigma, sigma_b, sigma_m)

  @classmethod
  def compute(cls, params, experiments, reflections):
    ''' Compute the profile models. '''
    from dials.algorithms.profile_model.model_list import ProfileModelList
    from dials.util.command_line import heading
    assert(len(experiments) > 0)

    print "=" * 80
    print ""
    print heading("Computing Profile Model")
    print ""

    # Split the reflections by experiment id
    if len(experiments) > 1:
      reflections_split = reflections.split_by_experiment_id()
      assert(len(reflections_split) == len(experiments))
    else:
      reflections_split = [reflections]

    # Compute the profile models
    min_zeta = params.gaussian_rs.filter.min_zeta
    profile_model_list = ProfileModelList()
    for exp, ref in zip(experiments, reflections_split):
      model = Factory.compute_single(exp, ref, min_zeta)
      print " Sigma_b: %.3f degrees" % model.sigma_b(deg=True)
      print " Sigma_m: %.3f degrees" % model.sigma_m(deg=True)
      profile_model_list.append(model)

    # Return the profile models
    return profile_model_list

  @classmethod
  def load(cls, params):
    ''' Load from phil parameters. '''
    from dials.algorithms.profile_model.model_list import ProfileModelList
    from dials.algorithms.profile_model.gaussian_rs import ProfileModel
    from math import pi
    assert(len(params.gaussian_rs.model) > 0)
    profile_model_list = ProfileModelList()
    for i in range(len(params.gaussian_rs.model)):
      profile_model_list.append(ProfileModel(
        params.gaussian_rs.model[i].n_sigma,
        params.gaussian_rs.model[i].sigma_b * pi / 180.0,
        params.gaussian_rs.model[i].sigma_m * pi / 180.0))
    return profile_model_list

  @classmethod
  def create(cls, params, experiments, reflections):
    ''' Create the profile models. '''
    if len(params.profile.gaussian_rs.model) > 0:
      assert(len(params.profile.gaussian_rs.model) == len(experiments))
      model = Factory.load(params.profile)
    else:
      assert(reflections is not None)
      model = Factory.compute(params.profile, experiments, reflections)
    return model