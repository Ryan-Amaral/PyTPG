"""
Needed because namedtuples need to be defined at the global level to work with
pickle, and declaring global in a function doesn't work because of some crazy
background stuff.
"""

from tpg.configuration.configurer import mutateParamKeys
from tpg.configuration.configurer import actVarKeys
from collections import namedtuple

# create the named tuple for each extra params thing
MutateParams = namedtuple("MutateParams", " ".join(mutateParamKeys))
ActVars = namedtuple("ActVars", " ".join(actVarKeys))
