import json
from Jumpscale import j


class package_manager(j.baseclasses.threebot_actor):
    def _init(self, gedis_server=None):
        assert gedis_server
        self._gedis_server = gedis_server

    def package_add(self, git_url=None, path=None, reload=True, schema_out=None, user_session=None):
        """
        ```in
        git_url = ""
        path = ""
        reload = true (B)
        ```
        can use a git_url or a path
        path needs to exist on the threebot server
        the git_url will get the code on the server (package source code) if its not there yet
        it will not update if its already there

        """

        user_session.admin_check()  # means will give error when not an admin user

        if git_url and path:
            raise j.exceptions.Input("add can only be done by git_url or name but not both")

        assert j.servers.threebot.current
        threebot_server_name = j.servers.threebot.current.name

        if git_url:
            p = git_url
        else:
            p = path

        def getname(p):
            path = j.clients.git.getContentPathFromURLorPath(p)
            path2 = "%s/meta.toml"
            name = None
            if j.sal.fs.exists(path2):
                meta = j.data.serializers.toml.loads(path2)
                if "name" in meta:
                    name = meta["name"]
            if not name:
                name = j.sal.fs.getBaseName(path).lower().strip()
            return name

        name = getname(p)

        if git_url:
            package = j.tools.threebot_packages.get(
                name=name, giturl=git_url, threebot_server_name=threebot_server_name
            )
        elif path:
            package = j.tools.threebot_packages.get(name=name, path=path, threebot_server_name=threebot_server_name)
        else:
            raise j.exceptions.Input("need to have git_url or path to package")

        if j.tools.threebot_packages.exists(name):
            package2 = j.tools.threebot_packages.get(name)
            if not package.path == package2.path:
                j.shell()
                raise j.exceptions.Input("package name is not unique:%s for %s" % (name, p))

        if reload == False and j.tools.threebot_packages.exists(name):
            return "OK"

        package.save()
        package.prepare()
        package.status = "INSTALLED"
        package.save()
        package.start()
        package.status = "RUNNING"
        package.save()

        if j.servers.threebot.current.web:
            # reload openresty configuration if web is enabled for this threebot server
            j.servers.threebot.current.openresty_server.reload()

        return "OK"

    def package_delete(self, name, schema_out=None, user_session=None):
        """
        ```in
        name = ""
        ```
        remove this package from the threebot
        will call package.uninstall()

        """
        user_session.admin_check()
        if not j.tools.threebot_packages.exists(name):
            return

        package = j.tools.threebot_packages.get(name)
        package.uninstall()
        package.delete()

    def package_stop(self, name, schema_out=None, user_session=None):
        """
        ```in
        name = ""
        ```
        stop a package, which means will call package.stop()
        """
        user_session.admin_check()
        if not j.tools.threebot_packages.exists(name):
            raise j.exceptions.NotFound("package not found", data={"name": name})

        package = j.tools.threebot_packages.get(name)
        package.stop()

    def package_start(self, name, schema_out=None, user_session=None):
        """
        ```in
        name = ""
        ```
        """
        user_session.admin_check()
        if not j.tools.threebot_packages.exists(name):
            raise j.exceptions.NotFound("package not found", data={"name": name})

        package = j.tools.threebot_packages.get(name)
        package.start()

    def package_disable(self, name, schema_out=None, user_session=None):
        """
        ```in
        name = ""
        ```
        """
        user_session.admin_check()
        if not j.tools.threebot_packages.exists(name):
            raise j.exceptions.NotFound("package not found", data={"name": name})

        package = j.tools.threebot_packages.get(name)
        package.disable()
