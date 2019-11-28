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

        if git_url:
            p = git_url
        else:
            p = path

        p = j.core.tools.text_replace(p)

        def getfullname(p):
            tomlpath = j.sal.fs.joinPaths(j.clients.git.getContentPathFromURLorPath(p), "package.toml")
            name_from_path = j.sal.fs.getBaseName(path).lower().strip()

            if j.sal.fs.exists(tomlpath):
                meta = j.data.serializers.toml.load(tomlpath)
                source = meta.get("source", {})
                threebot = source.get("threebot", "")
                name = source.get("name")
                if not name:
                    return name_from_path
                if threebot:
                    return f"{threebot}.{name}"
                return name
            return name_from_path

        name = getfullname(p)

        if git_url:
            package = j.tools.threebot_packages.get(name=name, giturl=git_url)
        elif path:
            package = j.tools.threebot_packages.get(name=name, path=path)
        else:
            raise j.exceptions.Input("need to have git_url or path to package")

        assert j.tools.threebot_packages.exists(name=package.name)

        if reload is False and package.status in ["installed"]:
            return "OK"
        try:
            package.install()
            package.save()
        except Exception as e:
            self._log_error(str(e), exception=e)
            return f"Could not add package {package.name}: {e}"

        # reload openresty configuration
        package.openresty.reload()

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
            # TODO: this does not seem to be ok, should use the main config in the package, not separate toml file
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
