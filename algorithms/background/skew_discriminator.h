/*
 * skew_discriminator.h
 *
 *  Copyright (C) 2013 Diamond Light Source
 *
 *  Author: James Parkhurst
 *
 *  This code is distributed under the BSD license, a copy of which is
 *  included in the root directory of this package.
 */
#ifndef DIALS_ALGORITHMS_BACKGROUND_SKEW_DISCRIMINATOR_H
#define DIALS_ALGORITHMS_BACKGROUND_SKEW_DISCRIMINATOR_H

#include "discriminator_strategy.h"

namespace dials { namespace algorithms {

  /**
   * A class that uses poisson distribution skew statistics to discriminate
   * between background and peak pixels in a reflection shoebox.
   */
  class SkewDiscriminator : public DiscriminatorStrategy {
  public:

    /** Initialise the class. */
    SkewDiscriminator() {}

    /**
     * Process the reflection list
     * @params reflections The list of reflections
     * @return Arrays of booleans True/False successful.
     */
    virtual flex_bool operator()(ReflectionList &reflections) const {
      return flex_bool();
    }
  };
}}

#endif /* DIALS_ALGORITHMS_BACKGROUND_SKEW_DISCRIMINATOR_H */
