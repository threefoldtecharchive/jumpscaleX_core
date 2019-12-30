from Jumpscale import j


class system(j.baseclasses.threebot_actor):
    def _init(self, **kwargs):
        assert self.package.gedis_server
        self._gedis_server = self.package.gedis_server
        j.data.schema.get_from_text(j.tools.threebot_packages._model.schema.text)

    def ping(self, user_session=None):
        return "PONG"

    def ping_bool(self, user_session=None):
        return True

    def jsx_schemas_get(self, user_session=None):
        """
        return all core schemas as understood by the server, is as text, can be processed by j.data.schema
        """
        out = ""
        urls = [
            "jumpscale.bcdb.user.2",
            "jumpscale.bcdb.circle.2",
            "jumpscale.bcdb.acl.2",
            "jumpscale.bcdb.acl.circle.2",
            "jumpscale.bcdb.acl.user.2",
            "jumpscale.gedis.server",
            "jumpscale.gedis.api",
            "jumpscale.gedis.cmd",
            "jumpscale.gedis.schema",
        ]

        schemas = {}
        for url in urls:
            s = j.data.schema.get_from_url(url)
            self._log_debug(s.url, data=s.text)
            schemas[s._md5] = (s.text, s.url)
        schemas = j.data.serializers.msgpack.dumps(schemas)
        return schemas

    def actors_add_path(self, path, user_session=None):
        self._gedis_server.actors_add(path)

    def api_meta_get(self, package_name=None, user_session=None):
        """
        return the api meta information

        """
        if isinstance(package_name, bytes):
            package_name = package_name.decode()
        # j.threebot.package_get
        if "." not in package_name:
            raise j.exceptions.Input("there should be . in package name, now:'%s'" % package_name)
        threebotauthor, package_name_short = package_name.split(".", 1)
        p = j.threebot.package_get(threebotauthor, package_name_short)
        p.actors  # will reload actors
        keys = [item for item in self._gedis_server.cmds_meta.keys() if item.startswith(package_name)]
        res = {"cmds": {}}
        for key in keys:
            val = self._gedis_server.cmds_meta[key]
            res["cmds"][key] = val.data._data
        return j.data.serializers.msgpack.dumps(res)

    # def filemonitor_paths(self, schema_out=None, user_session=None):
    #     """
    #     return all paths which should be monitored for file changes
    #     ```out
    #     paths = (LS)
    #     ```
    #     """
    #
    #     r = schema_out.new()
    #
    #     # monitor changes for the docsites (markdown)
    #     for key, item in j.tools.docsites.docsites.items():
    #         r.paths.append(item.path)
    #
    #     # monitor change for the webserver  (schema's are in there)
    #     r.paths.append(j.servers.web.latest.path)
    #
    #     # changes for the actors
    #     r.paths.append(self._gedis_server_gedis.code_generated_dir)
    #     r.paths.append(self._gedis_server_gedis.app_dir + "/actors")
    #     r.paths.append("%s/systemactors" % j.servers.gedis.path)
    #
    #     return r
    #
    # def filemonitor_event(self, changeobj):
    #     """
    #     used by filemonitor daemon to escalate events which happened on filesystem
    #
    #     ```in
    #     src_path = (S)
    #     event_type = (S)
    #     is_directory = (B)
    #     ```
    #
    #     """
    #
    #     # Check if a blueprint is changed
    #     # if changeobj.is_directory:
    #     #     path_parts = changeobj.src_path.split('/')
    #     #     if path_parts[-2] == 'blueprints':
    #     #         blueprint_name = "{}_blueprint".format(path_parts[-1])
    #     #         bp = j.servers.web.latest.app.app.blueprints.get(blueprint_name)
    #     #         if bp:
    #     #             self._log_info("reloading blueprint : {}".format(blueprint_name))
    #     #             del (j.servers.web.latest.app.app.blueprints[blueprint_name])
    #     #             j.servers.web.latest.app.app.register_blueself._log_info(bp)
    #     #             return
    #
    #     # Check if docsite is changed
    #     if changeobj.is_directory:
    #         docsites = j.tools.docsites.docsites
    #         for _, docsite in docsites.items():
    #             if docsite.path in changeobj.src_path:
    #                 docsite.load()
    #                 self._log_info("reloading docsite: {}".format(docsite))
    #                 return
    #
    #     # check if path is actor if yes, reload that one
    #     if not changeobj.is_directory and changeobj.src_path.endswith(".py"):
    #         paths = list()
    #         paths.append(self._gedis_server_gedis.code_generated_dir)
    #         paths.append(self._gedis_server_gedis.app_dir + "/actors")
    #         paths.append("%s/systemactors" % j.servers.gedis.path)
    #         # now check if path is in docsites, if yes then reload that docsite only !
    #         for path in paths:
    #             if path in changeobj.src_path:
    #                 actor_name = j.sal.fs.getBaseName(changeobj.src_path)[:-3].lower()
    #                 namespace = self._gedis_server_gedis.instance + "." + actor_name
    #                 if namespace in self._gedis_server_gedis.cmds_meta:
    #                     del self._gedis_server_gedis.cmds_meta[namespace]
    #                     del self._gedis_server_gedis.actors[namespace]
    #                     for cmd in list(self._gedis_server_gedis.cmds.keys()):
    #                         if actor_name in cmd:
    #                             del self._gedis_server_gedis.cmds[cmd]
    #                     self._gedis_server_gedis.cmds_add(namespace, path=changeobj.src_path)
    #                     self._log_info("reloading namespace: {}".format(namespace))
    #                     return
    #
    #     return
    #
    # def _options(self, args, nr_args=1):
    #     res = []
    #     res2 = {}
    #     key = ""
    #     nr = 0
    #     for arg in args:
    #         nr += 1
    #         if nr < nr_args + 1:
    #             val = args[nr - 1].decode()
    #             res.append(val)
    #             continue
    #         else:
    #             if key == "":
    #                 key = args[nr - 1].decode()
    #                 if not j.data.types.string.check(key):
    #                     raise j.exceptions.Base("%s: key:%s need to be string" % (args, key))
    #             else:
    #                 res2[key] = args[nr - 1].decode()
    #                 key = ""
    #     return res, res2
