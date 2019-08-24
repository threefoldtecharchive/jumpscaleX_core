# Markdown docsites:

[Docsites](docsites/README.md) are a collection of markdown documents, images and data files that can be generated using jumpscale `markdowndocs` tool.

The tool pre-process the given markdown directory (it adds some extension to markdown like custom link format and macros), also, it verifies and follows all the links and download it if needed, so you end up having a static directory that can be served using e.g. **openresty**.

### Markdown extensions:
* [Custom Link format](docsites/links.md) to make it easy to reference other documents and files.
* [Macros](docsites/macros/README.md):
    * [include](docsites/macros/include.md): to include content from other documents and files.
    * [dot](docsites/macros/dot.md): to directly convert DOT graph to an image.
    * [gslide](docsites/macros/gslide.md)
    * [slideshow](docsites/macros/slideshow.md)

## Tool usage

Given a markdown documents directory (a link to repository), the tool will pull, pre-process and generate the docsite.
You can find some markdown docs examples [here](https://github.com/threefoldtech/jumpscale_weblibs/tree/master/docsites_examples) and [here](https://github.com/threefoldtech/jumpscaleX/tree/development/docs/tools/wiki/docsites/examples/docs).

Usage example:

```python
url = "https://github.com/threefoldtech/jumpscaleX/tree/development/docs/tools/wiki/docsites/examples/docs"
docsite = j.tools.markdowndocs.load(url, name="test_example")
docsite.write()
```

This will pull the repo at the branch specified, then generate a docsite at `$DIR_VAR/docsites` with the name `test_example`.

To run a web server that listens on 8080 and serves this docsites as `/wiki/<docsite_name>` do:

`j.tools.markdowndocs.webserver()`


## Openresty
This docsite can be served as static files by nginx/openresty like:

```conf
worker_processes 4;
error_log stderr notice;
daemon off;
pid logs/nginx.pid;

events {
  worker_connections 1024;
}

http {
  include mime.types;
  client_body_buffer_size 64k;

  server {
    listen 8080;

    location /wiki_static/ {
      alias /sandbox/var/docsites/;
    }

}
```

## Docsites at the front-end
[docsite.js](https://github.com/threefoldtech/jumpscale_weblibs/blob/master/static/docsites/docsite.js) is a tool to replace custom handlebars in html templates with data and content from docsites.

To use it, make sure you add it to your html pages for example:

`<script src="/static/weblibs/docsites/docsite.js" type="text/javascript"></script>`

The directory where dociste are should be served at `/wiki_static`, see the [previous configuration](#Openresty) for openresty.

In any document, you can define a data section between `+++` like:

```
+++
name = "a new docsite to ..."
button = "<button>"
link1 = "https://...."
+++

any content can be added after.
```

and it can be referenced in the following format:

```
{{{ <docsite name>.[<path.to.document>].<variable name> }}}
```

* `<docsite name>`: the docsite name used when generating it using jumpscale markdown tool.
* `<path.to.document>`: is the path to the document, but it's a dot-separated.
* `<variable name>`: like `name`, `button` or `link1`.

the content can be referenced the same way, with a special name `content`:

```
{{{ <docsite name>.[<path.to.document>].content }}}
```

For example, if a docsite is generated at `/sandbox/var/docsites/site_a` and served using Openresty at `/wiki_static/site_a`, you can reference data and content in your html templates like:

```
<div class="container">
  <div class="content">
    {{{ site_a.[team.development].content }}}
  </div>
  <a href="{{{ site_a.[team.development].link1 }}}">Link to ...</a>
<div>
```

Some of our websites are based on this tool, [theefold.io](https://github.com/threefoldfoundation/www_threefold_lapis) is an example of using `lapis` with `etlua` templates and `docsite.js`.

## Wiki
You can serve any docsite that uses [docsify.js](https://docsify.js.org/#/?id=docsify) using our `lapis-wiki`, you just need to generate the docsite from your docs, and `lapis-wiki` will make it accessiable at `/wiki/<docsite name>`.

See [tool usage](#Tool-usage) to generate the docsite (you can find some examples in markdowndocs tool itself [here](https://github.com/threefoldtech/jumpscaleX/blob/development/Jumpscale/tools/markdowndocs/MarkDownDocs.py#L283)), and [lapis-wiki](https://github.com/threefoldfoundation/lapis-wiki) to run the web server.

## Openresty and lapis in action
* [lapis-wiki](https://github.com/threefoldfoundation/lapis-wiki): our implementation to serve docsites and other lapis applications.
* [Web server and gedis](https://github.com/threefoldtech/digitalmeX/tree/development/docs/webserver): how to run and serve files using openresty and lapis/lapis-wiki (with possible gedis backend).
* [Itsyou.online authentication](../../../Jumpscale/builder/web/docs/resty_iyo.md): itsyou.online authentication for resty
