from Jumpscale import j
import pycountry
import random

JSBASE = j.baseclasses.object


class Countries(j.baseclasses.object):
    __jslocation__ = "j.data.countries"

    @property
    def names(self):
        """Generates list of country names."""
        return [country.name for country in pycountry.countries]

    @property
    def random_country(self):
        """Generates a random country name"""
        return random.choice(self.names)
