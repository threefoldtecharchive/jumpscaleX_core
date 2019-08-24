import gevent
from Jumpscale import j


class open_publish(j.baseclasses.threebot_actor):
    def _init(self, **kwargs):
        # self.open_publish_tool = j.servers.threebot.default
        # gevent.spawn(self.open_publish_tool.auto_update)
        pass

    def publish_wiki(self, name, repo_url, domain, ip):
        """
        ```in
        name = ""
        repo_url = ""
        domain = ""
        ip = "" (ipaddr)
        ```
        :param name: name of the wiki
        :param domain: domain name of wiki i.e.: mywiki.com
        :param repo_url: repository url that contains the docs
        :param ip: ip which the domain should point to
        :return:
        """
        self.open_publish_tool.add_wiki(name, repo_url, domain, ip)
        return True

    def publish_website(self, name, repo_url, domain, ip):
        """
        ```in
        name = ""
        repo_url = ""
        domain = ""
        ip = "" (ipaddr)
        ```
        :param name: name of the website
        :param domain: domain name of website i.e.: mywebsite.com
        :param repo_url: repository url that contains the website files
        :param ip: ip which the domain should point to
        :return:
        """
        self.open_publish_tool.add_website(name, repo_url, domain, ip)
        return True

    def remove_wiki(self, name):
        """
        ```in
        name = ""
        ```
        :param name: name of the wiki
        :return:
        """
        self.open_publish_tool.remove_wiki(name)
        return True

    def remove_website(self, name):
        """
        ```in
        name = ""
        ```
        :param name: name of the website
        :return:
        """
        self.open_publish_tool.remove_website(name)
