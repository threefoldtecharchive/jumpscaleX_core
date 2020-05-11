# gedis http

exposing gedis as http endpoint using bottle server, so you can call some command on actor as the following using normal http `POST` requests

```bash
    POST /web/gedis/http/ACTOR_NAME/ACTOR_CMD
    json body:
    {
        args: {}
        content_type:..
        content_response:..
    }
```

## Simple example

```bash

~> curl -XPOST https://172.17.0.2/web/gedis/http/blog/get_tags -H "Content-Type: application/json" --insecure

["python", "lame", "markdown", "java"]

```

## Example with data

```bash

~> curl -i -XPOST https://172.17.0.2/web/gedis/http/blog/get_metadata --data '{"args":{"blog":"xmon"}}' -H "Content-Type: application/json" --insecure

HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 376
Date: Thu, 12 Sep 2019 16:01:13 GMT

{"blog_name": "xmon", "blog_title": "xmonader weblog", "blog_description": "let there be posts", "author_name": "ahmed", "author_email": "ahmed@there.com", "author_image_filename": "", "base_url": "", "url": "", "posts_dir": "/sandbox/code/gitlab/xmonader/sample-blog-jsx/posts", "github_username": "xmonader", "github_repo_url": "git@gitlab.com:xmonader/sample-blog-jsx.git"}

```

## Usage

For the all endpoint mapping check webinterface package docs [here](https://github.com/threefoldtech/jumpscaleX_threebot/blob/master/ThreeBotPackages/zerobot/webinterface/wiki/README.md)

### Package examples:

Check: [quick start](https://github.com/threefoldtech/jumpscaleX_threebot/blob/master/docs/quickstart.md)
