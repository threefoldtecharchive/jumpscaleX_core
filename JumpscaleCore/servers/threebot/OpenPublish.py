import os
import gevent
from Jumpscale import j

JSConfigClient = j.baseclasses.object_config
MASTER_BRANCH = "master"
DEV_BRANCH = "development"
DEV_SUFFIX = "_dev"


class OpenPublish(JSConfigClient):
    _SCHEMATEXT = """
        @url = jumpscale.open_publish.1
        name** = "" (S)
        websites = (LO) !jumpscale.open_publish.website.1
        wikis = (LO) !jumpscale.open_publish.wiki.1


        @url = jumpscale.open_publish.website.1
        name = "" (S)
        repo_url = "" (S)
        domain = "" (S)
        ip = "" (ipaddr)

        @url = jumpscale.open_publish.wiki.1
        name = "" (S)
        repo_url = "" (S)
        domain = "" (S)
        ip = "" (ipaddr)
    """

    def _init(self, **kwargs):
        self.open_publish_path = j.clients.git.getGitRepoArgs(OPEN_PUBLISH_REPO)[-3]
        self.gedis_server = None
        self.dns_server = None

    def auto_update(self):
        def update(objects):
            for obj in objects:
                self._log_info("Updating: {}".format(obj.name))
                self.load_site(obj, MASTER_BRANCH)
                self.load_site(obj, DEV_BRANCH, DEV_SUFFIX)

        # ensure nginx config files generated
        # for obj in self.wikis:
        #     self.generate_nginx_conf(obj)

        # for obj in self.websites:
        #     self.generate_nginx_conf(obj)
        self.reload_server()
        while True:
            update(self.wikis)
            update(self.websites)
            self._log_info("Reload for docsites done")
            gevent.sleep(300)

    def bcdb_get(self, name, secret="", use_zdb=False):
        zdb_std_client = None
        if use_zdb:
            zdb_admin_client = j.clients.zdb.client_admin_get(
                addr=self.zdb.host, port=self.zdb.port, secret=self.zdb.adminsecret_, mode=self.zdb.mode
            )
            zdb_std_client = zdb_admin_client.namespace_new(name, secret)
        bcdb = j.data.bcdb.get(name, zdb_std_client)
        return bcdb

    def load_site(self, obj, branch, suffix=""):
        try:
            dest = j.clients.git.getGitRepoArgs(obj.repo_url)[-3] + suffix
            j.clients.git.pullGitRepo(obj.repo_url, branch=branch, dest=dest)
            docs_path = "{}/docs".format(dest)
            doc_site = j.tools.markdowndocs.load(docs_path, name=obj.name + suffix)
            doc_site.write()
        except Exception as e:
            self._log_warning(e)

    def reload_server(self):
        cmd = "cd {0} && moonc . && lapis build".format(self.open_publish_path)
        j.tools.executorLocal.execute(cmd)

    def generate_nginx_conf(self, obj, reload=False, static_website=False):
        conf_base_path = j.sal.fs.getDirName(os.path.abspath(__file__))
        root_path = j.clients.git.getGitRepoArgs(obj.repo_url)[-3]
        if "website" in obj._schema.key:
            if static_website:
                config_path = j.sal.fs.joinPaths(conf_base_path, WEBSITE_STATIC_CONFIG_TEMPLATE)
            else:
                config_path = j.sal.fs.joinPaths(conf_base_path, WEBSITE_CONFIG_TEMPLATE)
        else:
            config_path = j.sal.fs.joinPaths(conf_base_path, WIKI_CONFIG_TEMPLATE)
        dest = j.sal.fs.joinPaths(self.open_publish_path, "vhosts", "{}.conf".format(obj.domain))
        args = {"name": obj.name, "domain": obj.domain, "root_path": root_path}
        j.tools.jinja2.file_render(path=config_path, dest=dest, **args)
        # handle if the tool used without using dns server
        if self.dns_server and obj.domain:
            if "wiki" in obj._schema.key:
                self.dns_server.resolver.create_record(domain="wiki." + obj.domain, value=obj.ip)
                self.dns_server.resolver.create_record(domain="wiki2." + obj.domain, value=obj.ip)
            else:
                self.dns_server.resolver.create_record(obj.domain, value=obj.ip)
                self.dns_server.resolver.create_record("www." + obj.domain, value=obj.ip)
                self.dns_server.resolver.create_record("www2." + obj.domain, value=obj.ip)
        if reload:
            self.reload_server()

    def add_wiki(self, name, repo_url, domain, ip):
        wiki = self.wikis.new(data=dict(name=name, repo_url=repo_url, domain=domain, ip=ip))

        # Generate md files for master and dev branches
        for branch in [DEV_BRANCH, MASTER_BRANCH]:
            suffix = DEV_SUFFIX if branch == DEV_BRANCH else ""
            self.load_site(wiki, branch, suffix)

        # Generate nginx config file for wiki
        self.generate_nginx_conf(wiki, reload=True)
        self.save()

    def add_website(self, name, repo_url, domain, ip):
        website = self.websites.new(data=dict(name=name, repo_url=repo_url, domain=domain, ip=ip))

        # Generate md files for master and dev branches
        for branch in [DEV_BRANCH, MASTER_BRANCH]:
            suffix = DEV_SUFFIX if branch == DEV_BRANCH else ""
            self.load_site(website, branch, suffix)

        # link website files into open publish dir
        repo_path = j.sal.fs.joinPaths(j.clients.git.getGitRepoArgs(repo_url)[-3])
        lapis_path = j.sal.fs.joinPaths(repo_path, "lapis")
        # If lapis dir not found, so the website is a pure static html website
        if not j.sal.fs.exists(lapis_path):
            # Generate nginx config file for website
            self.generate_nginx_conf(website, static_website=True, reload=True)
            self.save()
            return

        moon_files_path = j.sal.fs.joinPaths(lapis_path, "applications", name + ".moon")
        dest_path = j.sal.fs.joinPaths(self.open_publish_path, "applications", name + ".moon")
        j.sal.fs.symlink(moon_files_path, dest_path, overwriteTarget=False)

        static_path = j.sal.fs.joinPaths(lapis_path, "static", name)
        if j.sal.fs.exists(static_path):
            dest_path = j.sal.fs.joinPaths(self.open_publish_path, "static", name)
            j.sal.fs.symlink(static_path, dest_path, overwriteTarget=False)

        views_path = j.sal.fs.joinPaths(lapis_path, "views", name)
        if j.sal.fs.exists(views_path):
            dest_path = j.sal.fs.joinPaths(self.open_publish_path, "views", name)
            j.sal.fs.symlink(views_path, dest_path, overwriteTarget=False)

        # Load actors and chatflows if exists
        if self.gedis_server:
            actors_path = j.sal.fs.joinPaths(repo_path, "actors")
            if j.sal.fs.exists(actors_path):
                self.gedis_server.actors_add(actors_path, namespace=name)

            chatflows_path = j.sal.fs.joinPaths(repo_path, "chatflows")
            if j.sal.fs.exists(chatflows_path):
                self.gedis_server.chatbot.chatflows_load(chatflows_path)

        # Generate nginx config file for website
        self.generate_nginx_conf(website, static_website=False, reload=True)
        self.save()

    def remove_wiki(self, name):
        for i, wiki in enumerate(self.wikis):
            if name == wiki.name:
                dest = j.clients.git.getGitRepoArgs(wiki.repo_url)[-3]
                j.sal.fs.remove(dest)
                j.sal.fs.remove(dest + DEV_SUFFIX)
                j.sal.fs.remove(j.sal.fs.joinPaths(j.dirs.VARDIR, "docsites", wiki.name))
                j.sal.fs.remove(j.sal.fs.joinPaths(j.dirs.VARDIR, "docsites", wiki.name + DEV_SUFFIX))
                j.sal.fs.remove(j.sal.fs.joinPaths(self.open_publish_path, "vhosts", "{}.conf".format(wiki.domain)))
                if self.dns_server:
                    self.dns_server.resolver.delete_record("wiki." + wiki.domain, "A")
                    self.dns_server.resolver.delete_record("wiki2." + wiki.domain, "A")
                self.wikis.pop(i)
                self.save()
                self.reload_server()
                break
        else:
            raise j.exceptions.Value("No wiki found with this name: {}".format(name))

    def remove_website(self, name):
        for website in self.websites:
            if name == website.name:
                dest = j.clients.git.getGitRepoArgs(website.repo_url)[-3]
                j.sal.fs.remove(dest)
                j.sal.fs.remove(dest + DEV_SUFFIX)
                try:
                    j.sal.fs.remove(
                        j.sal.fs.joinPaths(self.open_publish_path, "vhosts", "{}.conf".format(website.domain))
                    )
                    j.sal.fs.remove(j.sal.fs.joinPaths(j.dirs.VARDIR, "docsites", website.name))
                    j.sal.fs.remove(j.sal.fs.joinPaths(j.dirs.VARDIR, "docsites", website.name + DEV_SUFFIX))
                except ValueError:
                    self._log_info("This website doesn't contain docsite to remove")

                try:
                    j.sal.fs.remove(j.sal.fs.joinPaths(self.open_publish_path, "static", name))
                    j.sal.fs.remove(j.sal.fs.joinPaths(self.open_publish_path, "views", name))
                    j.sal.fs.remove(j.sal.fs.joinPaths(self.open_publish_path, "applications", name + ".moon"))
                except ValueError:
                    self._log_info("This website doesn't contain lapis files to remove")
                self.websites.remove(website)
                self.save()
                self.reload_server()
                break
        else:
            raise j.exceptions.Value("No website found with this name: {}".format(name))
