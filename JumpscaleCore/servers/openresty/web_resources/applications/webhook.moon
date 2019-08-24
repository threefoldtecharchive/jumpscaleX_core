lapis = require "lapis"
util = require "lapis.util"
app = require "lapis.application"
str = require "resty.string"
redis = require 'lualib.redis'
config = require("lapis.config").get!


class WebHookApp extends lapis.Application

    [github: "/webhook/github"]: app.respond_to {
        POST: =>
            client = redis.connect(config.gedis_host, config.gedis_port)
            client["gedis"] = redis.command("default.webhook.pull_repo")
            if @req.headers['X-GitHub-Event'] != "push"
                ngx.log(ngx.WARN, "Wrong event type: ", @req.headers['X-GitHub-Event'])
                -- return status: ngx.HTTP_NOT_ACCEPTABLE

            if @req.headers['Content-Type'] != 'application/x-www-form-urlencoded'
                ngx.log(ngx.ERR, "wrong content type header: ", @req.headers['Content-Type'])
                return status: ngx.HTTP_NOT_ACCEPTABLE

            signature = @req.headers["X-Hub-Signature"]
            if signature == nil
                ngx.log(ngx.ERR, "No signature header found")
                return status: ngx.HTTP_BAD_REQUEST

            ngx.req.read_body()
            data = ngx.req.get_body_data()
            digest = "sha1=" .. str.to_hex(ngx.hmac_sha1(config.github_secret, data))

            if digest != signature
                ngx.log(ngx.ERR, "Invalid secret")
                return status: ngx.HTTP_UNAUTHORIZED

            payload = util.from_json(@req.params_post.payload)
            args = {
                "url": payload['repository']['ssh_url']
            }
            client.gedis(client, util.to_json(args))
            return status: ngx.HTTP_OK
    }
