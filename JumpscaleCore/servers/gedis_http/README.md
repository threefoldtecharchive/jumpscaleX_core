# gedis http

exposing gedis as http endpoint using bottle server, so you can call some command on actor as the following using normal http `POST` requests

```
    POST /actors/ACTOR_NAME/ACTOR_CMD 
    json body:
    {
        args: {}
        content_type:..
        content_response:..
    }
```

## Simple example 
```

~> curl -XPOST localhost:9201/actors/blog/get_tags
["python", "lame", "markdown", "java"] 

```

## Example with data
```
~> curl -i -XPOST localhost:9201/actors/blog/get_metadata --data '{"args":{"blog":"xmon"}}' -H "Content-Type: application/json"
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 376
Date: Thu, 12 Sep 2019 16:01:13 GMT

{"blog_name": "xmon", "blog_title": "xmonader weblog", "blog_description": "let there be posts", "author_name": "ahmed", "author_email": "ahmed@there.com", "author_image_filename": "", "base_url": "", "url": "", "posts_dir": "/sandbox/code/gitlab/xmonader/sample-blog-jsx/posts", "github_username": "xmonader", "github_repo_url": "git@gitlab.com:xmonader/sample-blog-jsx.git"}

```

## Usage

- create a website on openresty server
- create your locations as needed
- make sure to get the rack
- add gedishttp app to the rack 

### example in package

```python
        # website on openresty and its locations

        server = j.servers.openresty.get("blog")
        server.install(reset=False)
        server.configure()
        website = server.websites.get("blog")
        website.ssl = False
        website.port = 8084
        locations = website.locations.get("blog")

        website_location = locations.locations_static.new()
        website_location.name = "blog"
        website_location.path_url = f"/{blog_name}"
        website_location.use_jumpscale_weblibs = False
        fullpath = j.sal.fs.joinPaths(self.package_root, "html/")
        website_location.path_location = fullpath

        website_location_assets = locations.locations_static.new()
        website_location_assets.name = "assets"
        website_location_assets.path_url = "/"
        website_location_assets.use_jumpscale_weblibs = True
        fullpath = j.sal.fs.joinPaths(self.package_root, "html/")
        website_location_assets.path_location = fullpath


        ## START BOTTLE ACTORS ENDPOINT

        rack = j.servers.rack.get()
        # get gedis http server
        app = j.servers.gedishttp.get_app()

        # add gedis http server to the rack
        rack.bottle_server_add(name="gedishttp", port=9201, app=app)


        # create location `/actors` to on your website `8084` to forward
        # requests to `9201` where the bottle server is running
        proxy_location = locations.locations_proxy.new()
        proxy_location.name = "gedishttp"
        proxy_location.path_url = "/actors"
        proxy_location.ipaddr_dest = "0.0.0.0"
        proxy_location.port_dest = 9201
        proxy_location.scheme = "http"
        ## END BOTTLE ACTORS ENDPOINT


        locations.configure()
        website.configure()

```