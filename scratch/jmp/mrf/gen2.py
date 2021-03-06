
from __future__ import division

def mean_and_variance(a):
  sum1 = sum(a)
  sum2 = sum(aa*aa for aa in a)
  mean = sum1 / len(a)
  variance = (sum2 - sum1*sum1/len(a)) / len(a)
  return mean, variance


def sign(x):
  if x == 0:
    return 0
  elif x < 0:
    return -1
  return 1

def F(p, n, alpha=0.05):
  from scipy.stats import f
  d1 = p
  d2 = n - p
  return f(d1, d2).ppf(1 - alpha)


def glm(x, p = None):
  from math import exp , sqrt, log, factorial, lgamma
  from scitbx import matrix
  from scipy.stats import poisson
  beta0 = 0

  if p is None:
    p = [1.0] * len(x)

  while True:
    n = beta0
    mu = exp(n)
    z = [n + (xx - mu) / mu for xx in x]
    w = [pp * mu for pp in p]

    W = matrix.diag(w)
    Z = matrix.col(z)
    X = matrix.rec([1]*len(z), (len(z),1))

    beta = (X.transpose() * W * X).inverse() * X.transpose()*W*z

    if abs(beta[0] - beta0) < 1e-3:
      break
    beta0 = beta[0]

  n = beta[0]
  mu = exp(n)
  z = [n + (xx - mu) / mu for xx in x]
  w = [pp * mu for pp in p]

  W = matrix.diag(w)
  Z = matrix.col(z)
  X = matrix.rec([1]*len(z), (len(z),1))
  W12 = matrix.diag([sqrt(ww) for ww in w])
  H = X * (X.transpose()*W*X).inverse() * X.transpose()

  r = [(xx - mu) / mu for xx in x]
  sum1 = 0
  sum2 = 0
  sum3 = 0
  D = []
  for xx in x:
    d = 0
    if xx != 0:
      d += xx * log(xx)
      d -= xx * log(mu)
    d -= (xx - mu)
    D.append(2*d)
  # r = []
  # for xx in x:
  #   if xx == 0:
  #     r.append(0)
  #   else:
  #     r.append(2*(log(xx) - log(mu)))
  # D = []
  # for i in range(len(r)):
  #   h = H[i+i*H.n[0]]
  #   d = (r[i]/(1 - h))**2 * h/1.0
  #   D.append(d)

  # print min(x), max(x)
  print min(D), max(D), F(1, len(x))

  return exp(beta[0]), max(D) > F(1, len(x))

def residuals(mu, x):
  return [(xx - mu)/mu for xx in x]

def ts(x):
  from numpy import median
  return median(x)

def ts2(x):
  from numpy import median
  from dials.array_family import flex
  r = flex.double(flex.grid(len(x), len(x)))
  for j in range(len(x)):
    for i in range(len(x)):
      r[j,i] = (x[i] + x[j]) / 2.0


  from matplotlib import pylab
  pylab.imshow(r.as_numpy_array())
  pylab.show()
  return median(r)

def glm_iter(x):

  p = 1

  B0, OUT = glm(x)


  # B1 = [glm(x[:i] + x[i+1:]) for i in range(len(x))]
  # R1 = [residuals(b1, x) for b1 in B1]

  # D = []
  # for b1 in B1:

  #   D.append((len(x) * (B0-b1)**2) / (p*MSE))

  return OUT



if __name__ == '__main__':

  from dials.array_family import flex
  from random import uniform
  from numpy.random import poisson, seed
  seed(0)
  means1 = []
  means2 = []
  for k in range(100):
    print k
    a = list(poisson(0.1, 100))
    print a
    # a[4] = 10
    # a[50] = 10
    means1.append(sum(a)/len(a))
    means2.append(ts2(a))
  print "Outliers: ", means2.count(True)

  from matplotlib import pylab
  print "MOM1: ", sum(means1) / len(means1)
  pylab.plot(means1, color='black')
  pylab.plot(means2, color='blue')
  pylab.show()
