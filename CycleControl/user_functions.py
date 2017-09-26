import math

def constFunc(domain, end, A):
    # A is the constant value
    return [A] * (len(domain))


def linFunc(domain, end, A, B):
    # A is the starting value, B is the final value
    result = []
    amp = (B - A) / (end - domain[0])
    for i in domain:
        result.append(amp * (i - domain[0]) + A)
    return result


def sinFunc(domain, end, A, B, C):
    # A is the amplitude, B is the frequency, C is the phase in radians
    result = []
    for i in domain:
        result.append(A * math.sin(B * i + C))
    return result


def expFunc(domain, end, A, B, C):
    # A is the initial value, B is the final value, C is the time constant
    result = []
    offset = A + (B - A) / (1 - math.exp((end - domain[0]) / C))
    amplitude = (A - B) / (math.exp(domain[0] / C) * (1 - math.exp((end - domain[0]) / C)))
    for i in domain:
        result.append(amplitude * math.exp(i / C) + offset)
    return result

FUNCTION_MAP = {
    'const': constFunc,
    'ramp': linFunc,
    'sin': sinFunc,
    'exp': expFunc,
}