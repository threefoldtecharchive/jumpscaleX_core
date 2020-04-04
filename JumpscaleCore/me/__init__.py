from .Me import Me
from .MeIdentities import MeIdentities
from Jumpscale import j

j._meClass = Me
j.me_identities = MeIdentities()
