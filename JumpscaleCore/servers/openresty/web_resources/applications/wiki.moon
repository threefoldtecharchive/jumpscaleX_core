lapis = require "lapis"
common = require "applications/wiki/common"


class WikiApp extends lapis.Application
    @enable "etlua"

    "/(wiki/:doc_site)": =>
        -- Check if the request is coming from a domain or using the local path /wiki
        if @params.doc_site
            @name = @params.doc_site
        else
            @name = ngx.var.name

        -- build the websocket url
        scheme = "ws"
        req = @req.parsed_url
        if @req.headers['x-forwarded-proto'] == "https"
            @req.parsed_url.scheme = "https"
            scheme = "wss"
        @url = scheme .. "://" .. req.host
        if req.port
            @url = @url .. ":" .. 4444

        @metadata = common.load_metadata(@name)
        return render: "wiki.index", layout: false
