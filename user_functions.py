import numpy as np

def constFunc(domain, end, A):
    # A is the constant value
    domain = np.array(domain)
    return [A] * (len(domain))


def linFunc(domain, end, A, B):
    # A is the starting value, B is the final value
    domain = np.array(domain)
    return (B - A) / (end - domain[0]) * (domain - domain[0]) + A


def sinFunc(domain, end, A, B, C):
    # A is the amplitude, B is the frequency, C is the phase in radians
    domain = np.array(domain)
    return A * np.sin(B * domain + C)


def expFunc(domain, end, A, B, C):
    # A is the initial value, B is the final value, C is the time constant
    domain = np.array(domain)
    offset = A + (B - A) / (1 - np.exp((end - domain[0]) / C))
    amplitude = (A - B) / (np.exp(domain[0] / C) * (1 - np.exp((end - domain[0]) / C)))
    return amplitude * np.exp(domain / C) + offset