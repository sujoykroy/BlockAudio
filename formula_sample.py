import numpy

def formula1(d, t, bt):
    return numpy.sin(bt*numpy.pi*2)*d.p(t*2)*d.p2(t)*2.5

def formula2(d, t, bt):
    m = 3
    return formula1(d,t,bt) + formula1(d, t, m*bt)

formulas=[
    formula1
]

