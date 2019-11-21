import json
from Jumpscale import j


class package_manager(j.baseclasses.threebot_actor):
    def _init(self, gedis_server=None):
        assert gedis_server
        self._gedis_server = gedis_server
        j.data.schema.get_from_text(j.tools.threebot_packages._model.schema.text)

    @j.baseclasses.actor_method
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

        assert j.threebot.servers.core
        threebot_server_name = j.threebot.servers.core.name

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
                raise j.exceptions.Input("package name is not unique:%s for %s" % (name, p))

        if reload is False and j.tools.threebot_packages.exists(name):
            return "OK"
        try:
            package.save()
            package.prepare()
            package.status = "INSTALLED"
            package.save()
            package.start()
            package.status = "RUNNING"
            package.save()
        except Exception as e:
            self._log_error(str(e), exception=e)
            return f"Could not add package {package.name}: {e}"

        # reload openresty configuration
        j.threebot.servers.core.openresty_server.reload()

        return "OK"

    @j.baseclasses.actor_method
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

    @j.baseclasses.actor_method
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

    @j.baseclasses.actor_method
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

    @j.baseclasses.actor_method
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

    @j.baseclasses.actor_method
    def package_enable(self, name, schema_out=None, user_session=None):
        """
        ```in
        name = ""
        ```
        """
        user_session.admin_check()
        if not j.tools.threebot_packages.exists(name):
            raise j.exceptions.NotFound("package not found", data={"name": name})

        package = j.tools.threebot_packages.get(name)
        package.enable()

    @j.baseclasses.actor_method
    def packages_list(self, frontend=False, schema_out=None, user_session=None):
        """
        ```in
        frontend = (B) false  # list only frontend packages
        ```

        ```out
        packages = (LO) !jumpscale.threebot.package.1
        ```
        """
        packages = []
        for package in j.tools.threebot_packages.find():
            if frontend:
                mdp = j.sal.fs.joinPaths(package.path, "meta.toml")
                if j.sal.fs.exists(mdp):
                    metadata = j.data.serializers.toml.loads(j.sal.fs.readFile(mdp))
                    if not metadata.get("frontend", False):
                        continue
                else:
                    continue

            packages.append(package)

        out = schema_out.new()
        out.packages = packages
        return out
