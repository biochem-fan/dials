
#ifndef DIALS_ALGORITHMS_INTEGRATION_PREPROCESSOR_H
#define DIALS_ALGORITHMS_INTEGRATION_PREPROCESSOR_H

#include <string>
#include <sstream>
#include <iostream>
#include <iomanip>
#include <algorithm>
#include <dials/array_family/reflection_table.h>
#include <dials/algorithms/reflection_basis/coordinate_system.h>


namespace dials { namespace algorithms {

  class Preprocessor {
  public:

    Preprocessor(af::reflection_table reflections)
        : num_total_(0),
          num_strong_(0),
          num_filtered_(0),
          num_integrate_(0),
          num_overlap_bg_(0),
          num_overlap_fg_(0),
          num_icering_(0),
          num_clipped_(0),
          nums_overlap_bg_(0),
          nums_overlap_fg_(0),
          nums_icering_(0),
          nums_reference_(0),
          small_x_(0),
          small_y_(0),
          small_z_(0),
          large_x_(0),
          large_y_(0),
          large_z_(0) {

      // Check reflection table contains expected properties
      DIALS_ASSERT(reflections.is_consistent());
      DIALS_ASSERT(reflections.contains("flags"));
      DIALS_ASSERT(reflections.contains("id"));
      DIALS_ASSERT(reflections.contains("panel"));
      DIALS_ASSERT(reflections.contains("miller_index"));
      DIALS_ASSERT(reflections.contains("entering"));
      DIALS_ASSERT(reflections.contains("s1"));
      DIALS_ASSERT(reflections.contains("xyzcal.px"));
      DIALS_ASSERT(reflections.contains("xyzcal.mm"));
      DIALS_ASSERT(reflections.contains("bbox"));
      DIALS_ASSERT(reflections.contains("zeta"));
      DIALS_ASSERT(reflections.contains("d"));

      // Get some arrays needed for preprocessing
      af::ref<std::size_t> flags = reflections["flags"];
      af::const_ref<std::size_t> id = reflections["id"];
      af::const_ref< vec3<double> > s1 = reflections["s1"];
      af::const_ref<int6> bbox = reflections["bbox"];
      af::const_ref<double> zeta = reflections["zeta"];
      af::const_ref<double> d = reflections["d"];

      // Compute some summary stuff
      num_total_ = reflections.size();
      for (std::size_t i = 0; i < bbox.size(); ++i) {

        // Filter the reflections by zeta
        if (std::abs(zeta[i]) > 0.05) {
          flags[i] |= af::DontProcess;
          flags[i] &= ~af::ReferenceSpot;
        }

        // Check if reflections are predicted on ice rings


        // Check the flags
        if (flags[i] & af::ReferenceSpot) {
          num_strong_++;
        }
        if (flags[i] & af::DontProcess) {
          num_filtered_++;
        } else {
          num_integrate_++;
        }

        // Compute stuff about the bounding box
        int6 b = bbox[i];
        DIALS_ASSERT(b[1] > b[0]);
        DIALS_ASSERT(b[3] > b[2]);
        DIALS_ASSERT(b[5] > b[4]);
        if (i == 0) {
          small_x_ = large_x_ = (std::size_t)(b[1] - b[0]);
          small_y_ = large_y_ = (std::size_t)(b[3] - b[2]);
          small_z_ = large_z_ = (std::size_t)(b[5] - b[4]);
        } else {
          small_x_ = std::min(small_x_, (std::size_t)(b[1] - b[0]));
          small_y_ = std::min(small_y_, (std::size_t)(b[3] - b[2]));
          small_z_ = std::min(small_z_, (std::size_t)(b[5] - b[4]));
          large_x_ = std::max(large_x_, (std::size_t)(b[1] - b[0]));
          large_y_ = std::max(large_y_, (std::size_t)(b[3] - b[2]));
          large_z_ = std::max(large_z_, (std::size_t)(b[5] - b[4]));
        }
      }
    }

    std::string summary() const {

      // Helper to print a percent
      struct percent {
        double p_;
        percent(double p) : p_(p) {}
        std::string s() const {
          std::stringstream ss;
          ss << std::setprecision(2) << p_ << "%";
          return ss.str();
        }
      };

      // Helper to print a number and percent
      struct number_and_percent {
        std::size_t t_;
        number_and_percent(std::size_t t) : t_(t) {}
        std::string s(std::size_t n) const {
          DIALS_ASSERT(n >= 0 && n <= t_);
          double p = t_ > 0 ? n / t_ : 0.0;
          std::stringstream ss;
          ss << n << " (" << percent(p).s() << ") ";
          return ss.str();
        }
      };

      // Format the summary output
      number_and_percent nt(num_total_);
      number_and_percent ns(num_strong_);
      std::stringstream ss;
      ss <<
        "Preprocessed reflections:\n"
        "\n"
        " Number of reflections:                  " << num_total_ << "\n"
        " Number of strong reflections:           " << num_strong_ << "\n"
        " Number filtered with zeta:              " << nt.s(num_filtered_) << "\n"
        " Number of reflection to integrate:      " << nt.s(num_integrate_) << "\n"
        " Number overlapping (background):        " << nt.s(num_overlap_bg_) << "\n"
        " Number overlapping (foreground):        " << nt.s(num_overlap_fg_) << "\n"
        " Number recorded on ice rings:           " << nt.s(num_icering_) << "\n"
        " Number clipped at task boundaries:      " << nt.s(num_clipped_) << "\n"
        " Number strong overlapping (background): " << ns.s(nums_overlap_bg_) << "\n"
        " Number strong overlapping (foreground): " << ns.s(nums_overlap_fg_) << "\n"
        " Number strong recorded on ice rings:    " << ns.s(nums_icering_) << "\n"
        " Number strong for reference creation:   " << ns.s(nums_reference_) << "\n"
        " Smallest measurement box size (x):      " << small_x_ << "\n"
        " Smallest measurement box size (y):      " << small_y_ << "\n"
        " Smallest measurement box size (z):      " << small_z_ << "\n"
        " Largest measurement box size (x):       " << large_x_ << "\n"
        " Largest measurement box size (y):       " << large_y_ << "\n"
        " Largest measurement box size (z):       " << large_z_ << "\n"
        ;
      return ss.str();
    }

  private:
    std::size_t num_total_;
    std::size_t num_strong_;
    std::size_t num_filtered_;
    std::size_t num_integrate_;
    std::size_t num_overlap_bg_;
    std::size_t num_overlap_fg_;
    std::size_t num_icering_;
    std::size_t num_clipped_;
    std::size_t nums_overlap_bg_;
    std::size_t nums_overlap_fg_;
    std::size_t nums_icering_;
    std::size_t nums_reference_;
    std::size_t small_x_;
    std::size_t small_y_;
    std::size_t small_z_;
    std::size_t large_x_;
    std::size_t large_y_;
    std::size_t large_z_;
  };

}}

#endif // DIALS_ALGORITHMS_INTEGRATION_PREPROCESSOR_H