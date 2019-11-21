from Jumpscale import j

JSConfigClient = j.baseclasses.object_config


class SonicClient(JSConfigClient):
    """
    Sonic server client

    usage example:-

    data = { 
         'post:1': "this is some test text hello", 
         'post:2': 'this is a hello world post', 
         'post:3': "hello how is it going?", 
         'post:4': "for the love of god?", 
         'post:5': "for the love lorde?", 
     } 
     client = j.clients.sonic.get('main', host="127.0.0.1", port=1491, password='dmdm') 
     for articleid, content in data.items(): 
         client.push("forum", "posts", articleid, content) 
     print(client.query("forum", "posts", "love")) 

    # ['post:5', 'post:4']

    print(client.suggest("forum", "posts", "lo"))                                
    # ['lorde', 'love']



    """

    _SCHEMATEXT = """
        @url =  jumpscale.sonic.client
        name** = "" (S)
        host = "127.0.0.1" (S)
        port = 1491 (I)
        password = "" (S)
        """

    def _init(self, **kwargs):
        self._cached_client_search = None
        self._cached_client_ingest = None
        self._bufsize = None

        self.push = self._client_ingest.push
        self.pop = self._client_ingest.pop
        self.count = self._client_ingest.count
        self.flush = self._client_ingest.flush
        self.flush_collection = self._client_ingest.flush_collection
        self.flush_bucket = self._client_ingest.flush_bucket
        self.flush_object = self._client_ingest.flush_object

        self.query = self._client_search.query
        self.suggest = self._client_search.suggest

    @property
    def _client_search(self):
        try:
            from sonic import SearchClient, IngestClient
        except ImportError:
            j.builders.runtimes.python3.pip_package_install("sonic-client")
            from sonic import SearchClient, IngestClient

        if not self._cached_client_search:
            self._cached_client_search = SearchClient(host=self.host, port=self.port, password=self.password)
        return self._cached_client_search

    @property
    def _client_ingest(self):
        try:
            from sonic import SearchClient, IngestClient
        except ImportError:
            j.builders.runtimes.python3.pip_package_install("sonic-client")
            from sonic import SearchClient, IngestClient

        if not self._cached_client_ingest:
            self._cached_client_ingest = IngestClient(host=self.host, port=self.port, password=self.password)
        return self._cached_client_ingest

    @property
    def bufsize(self):
        if not self._bufsize:
            self._bufsize = self._client_ingest.get_active_connection().bufsize
        return self._bufsize
