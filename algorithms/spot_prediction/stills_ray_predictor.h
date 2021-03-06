/*
 * stills_ray_predictor.h
 *
 *  Copyright (C) 2013 Diamond Light Source, CCP4
 *
 *  Author: David Waterman
 *  Author: James Parkhurst
 *
 *  This code is distributed under the BSD license, a copy of which is
 *  included in the root directory of this package.
 */

#ifndef DIALS_ALGORITHMS_SPOT_PREDICTION_STILLS_RAY_PREDICTOR_H
#define DIALS_ALGORITHMS_SPOT_PREDICTION_STILLS_RAY_PREDICTOR_H

#include <cmath>
#include <cctbx/miller.h>
#include <scitbx/array_family/small.h>
#include <scitbx/vec3.h>
#include <scitbx/mat3.h>
#include <dials/array_family/scitbx_shared_and_versa.h>
#include <dials/model/data/ray.h>
#include <dials/error.h>

namespace dials { namespace algorithms {

  using std::sqrt;
  using scitbx::vec3;
  using scitbx::mat3;
  using dials::model::Ray;

  /**
   *  Predict for a relp based on the current states of models of the
   *  experimental geometry. Here we assume the crystal UB already puts hkl in
   *  reflecting position, so no rotation is required.
   *
   *  Generally, this assumption is not true: most relps are not touching the
   *  Ewald sphere on a still image, but are observed due to their finite
   *  mosaicity and the finite width of the Ewald sphere. Rather than employing
   *  a complicated polychromatic and mosaic model, here we take a naive
   *  approach, which is likely to introduce (small?) errors in the direction of
   *  predicted rays.
   */
  class StillsRayPredictor {
  public:

    typedef cctbx::miller::index<> miller_index;

    StillsRayPredictor(vec3<double> s0)
      : s0_(s0) {
      DIALS_ASSERT(s0_.length() > 0.0);
      unit_s0_ = s0_.normalize();
    }

    Ray operator()(miller_index h, mat3<double> ub) {

      // Calculate the reciprocal space vector and required unit vectors
      vec3<double> q = ub * h;
      vec3<double> e1 = q.cross(unit_s0_).normalize();
      vec3<double> c0 = unit_s0_.cross(e1).normalize();

      // Calculate the vector rotated to the Ewald sphere
      double qq = q.length_sq();
      double lambda = 1. / s0_.length();
      double a = 0.5 * qq * lambda;
      double tmp = qq - a*a;
      DIALS_ASSERT(tmp > 0.0);
      double b = std::sqrt(tmp);
      vec3<double> r = -1.0 * a * unit_s0_ + b * c0;

      // Calculate delpsi value
      vec3<double> q0 = q.normalize();
      vec3<double> q1 = q0.cross(e1).normalize();
      delpsi_ = -1.0 * atan2(r*q1, r*q0);

      // Calculate the Ray (default zero angle and 'entering' as false)
      vec3<double> s1 = (s0_ + r).normalize() * s0_.length();
      return Ray(s1, 0.0, false);
    }

    double get_delpsi() const {
      return delpsi_;
    }

  private:
    vec3<double> s0_;
    vec3<double> unit_s0_;
    double delpsi_;
  };

}} // namespace dials::algorithms

#endif // DIALS_ALGORITHMS_SPOT_PREDICTION_STILLS_RAY_PREDICTOR_H
