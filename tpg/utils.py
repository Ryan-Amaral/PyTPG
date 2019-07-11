import random

"""
Various useful functions for use within TPG, and for using TPG.
"""

"""
Coin flips, at varying levels of success based on prob.
"""
def flip(prob):
    return random.uniform(0.0,1.0) < prob
