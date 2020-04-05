from .Me import Me
from .MyIdentities import MyIdentities
from Jumpscale import j

j._meClass = Me
j.myidentities = MyIdentities()
