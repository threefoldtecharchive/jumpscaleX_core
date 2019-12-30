from Jumpscale import j


class wiki_content(j.baseclasses.threebot_actor):
    @j.baseclasses.actor_method
    def reload(self, wiki_name, user_session, schema_out):
        """
        :param name: name of the wiki to reload

        ```in
        wiki_name = (S)
        ```
        """
        j.tools.markdowndocs.reload(wiki_name)

    @j.baseclasses.actor_method
    def load(self, wiki_name, wiki_url, pull, download, user_session, schema_out):
        """
        ```in
        wiki_name = (S)
        wiki_url = (S)
        pull = false (B)
        download = false (B)
        ```
        """

        def load_wiki(wiki_name, wiki_url, pull=False, download=False):
            wiki = j.tools.markdowndocs.load(path=wiki_url, name=wiki_name, pull=pull, download=download)
            wiki.write()

        queues = ["content_wiki_load"]
        job = j.servers.myjobs.schedule(
            load_wiki, return_queues=queues, wiki_name=wiki_name, wiki_url=wiki_url, pull=pull, download=download
        )
        j.servers.myjobs.wait_queues(queue_names=queues, size=len([job.id]))
