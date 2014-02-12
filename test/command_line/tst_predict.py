
from __future__ import division


class Test(object):

  def __init__(self):
    from os.path import join
    from dials.array_family import flex
    import libtbx.load_env
    try:
      dials_regression = libtbx.env.dist_path('dials_regression')
    except KeyError, e:
      print 'FAIL: dials_regression not configured'
      exit(0)

    self.path = join(dials_regression, "prediction_test_data")

  def run(self):

    self.tst_static_prediction()
    self.tst_scan_varying_prediction()

  def tst_static_prediction(self):
    from os.path import abspath, join
    from libtbx import easy_run

    # Call dials.integrate
    easy_run.fully_buffered([
      'dials.predict',
      join(self.path, 'experiments_scan_static_crystal.json'),
    ]).raise_if_errors()

    import cPickle as pickle
    table = pickle.load(open('predicted.pickle', 'rb'))
    assert(len(table) == 1994)
    print 'OK'

    # Check the reflection IDs
    assert('id' in table)
    assert('miller_index' in table)
    assert('s1' in table)
    assert('xyzcal.px' in table)
    assert('xyzcal.mm' in table)
    for r in table:
      assert(r['id'] == 0)

    print 'OK'

  def tst_scan_varying_prediction(self):
    from os.path import abspath, join
    from libtbx import easy_run

    # Call dials.integrate
    easy_run.fully_buffered([
      'dials.predict',
      join(self.path, 'experiments_scan_varying_crystal.json'),
    ]).raise_if_errors()

    import cPickle as pickle
    table = pickle.load(open('predicted.pickle', 'rb'))
    assert(len(table) == 1934)
    print 'OK'

    # Check the reflection IDs
    assert('id' in table)
    assert('miller_index' in table)
    assert('s1' in table)
    assert('xyzcal.px' in table)
    assert('xyzcal.mm' in table)
    for r in table:
      assert(r['id'] == 0)

    print 'OK'


if __name__ == '__main__':
  test = Test()
  test.run()
