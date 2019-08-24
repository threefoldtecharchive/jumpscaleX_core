lapis = require "lapis"
  
class ChatApp extends lapis.Application
    @enable "etlua"

    [root: "/chat"]: =>
        render: "chat.home"

    [index: "/chat/session/:topic"]: =>
        req = @req.parsed_url
        scheme = "ws"
        if req.scheme == "https" or @req.headers['x-forwarded-proto'] == "https"
            scheme = "wss"
        @url = scheme .. "://" .. req.host
        if req.port
            @url = @url .. ":" .. 4444
        @topic = @params.topic
        render: "chat.index"
