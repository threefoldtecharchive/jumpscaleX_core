# gedis http

exposing gedis as http endpoint using bottle server, so you can call some command on actor as the following using normal http `POST` requests

```bash
    POST /<threebot_name>/<package_name>/actors/<name>/<cmd>
    json body:
    {
        args: {},
        content_type: 'json',
        content_response: 'json'
    }
```

## Simple example

```bash

~> curl -XPOST https://172.17.0.2/zerobot/blog/actors/blog/get_tags -H "Content-Type: application/json" --insecure

["python", "lame", "markdown", "java"]

```

## Example with data

```bash

~> curl -i -XPOST https://172.17.0.2/zerobot/blog/actors/blog/get_metadata --data '{"args":{"blog":"xmon"}}' -H "Content-Type: application/json" --insecure

HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 376
Date: Thu, 12 Sep 2019 16:01:13 GMT

{"blog_name": "xmon", "blog_title": "xmonader weblog", "blog_description": "let there be posts", "author_name": "ahmed", "author_email": "ahmed@there.com", "author_image_filename": "", "base_url": "", "url": "", "posts_dir": "/sandbox/code/gitlab/xmonader/sample-blog-jsx/posts", "github_username": "xmonader", "github_repo_url": "git@gitlab.com:xmonader/sample-blog-jsx.git"}

```

## Usage

For the all endpoint mapping check webinterface package docs [here](https://github.com/threefoldtech/jumpscaleX_threebot/blob/development/ThreeBotPackages/zerobot/webinterface/wiki/README.md)

### Package examples:

Check: [quick start](https://github.com/threefoldtech/jumpscaleX_threebot/blob/development/docs/quickstart.md)
