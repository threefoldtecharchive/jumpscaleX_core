from .Location import render_config_template, Locations

from Jumpscale import j


class Website(j.baseclasses.factory_data):
    """
    Website hosted in openresty
    This is port / hostname combination

    it will include locations from

    {DIR_BASE}/cfg/

    """

    _CHILDCLASSES = [Locations]

    _SCHEMATEXT = """
        @url = jumpscale.openresty.website
        name** = (S)
        port = 80 (I)
        ssl = True (B)
        domain = ""
        path = ""
        mother_id** = 0 (I)
        """

    @property
    def path_cfg_dir(self):
        return f"{self._parent._parent.path_cfg_dir}/servers"

    @property
    def path_cfg(self):
        return f"{self.path_cfg_dir}/{self.name}.http.conf"

    @property
    def path_web(self):
        return self._parent._parent.path_web

    @property
    def path_web_default(self):
        return self._parent._parent.path_web_default

    def configure(self):
        """
        if config none then will use self.CONFIG

        config is a server config file of nginx (in text format)

        see `CONFIG` for an example.

        can use template variables with website...  (obj is this obj = self)


        :param config:
        :return:
        """

        j.sal.fs.createDir(self.path_cfg_dir)
        config = render_config_template("website", base_dir=j.dirs.BASEDIR, website=self)
        j.sal.fs.writeFile(self.path_cfg, config)

        for locationsconfigs in self.locations.find():
            locationsconfigs.configure()


class Websites(j.baseclasses.object_config_collection):

    _CHILDCLASS = Website
