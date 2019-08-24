# Macros
Macros are custom extension to markdown syntax that take some input from user, then produces some markdown as an output.

For example, `include` macro can include any markdown or content from anohter document or file (even in another repository or wiki).

Any macro starts with `!!!` like ```!!!include(...)```. Sometimes it need some input data, this data can be passed in two ways, using function style like:

```
!!!include("link_to_doc.md")
```

or using toml (inside a code block)

````
```
!!!include
link = "link_to_doc.md"
header_level_modify = 1
```
````

### Errors

When executing any macro, errors can occur, in such case, they are saved in a document called`errors.md` in the root directory of the docsite, it can be accessed normally by th link `<wiki or website link>/#/errors.md`. The content will be a listing of errors occured when pre-processing all of markdown documents.


### List of available macros
* [include](include.md): to include content from other documents or files.
* [dot](dot.md): to convert [DOT](https://en.wikipedia.org/wiki/DOT_(graph_description_language)) graphs to images directly from blocks.
* [team](team.md): for team member listing (with data from another repository).
* [gallery](gallery.md): to create a gallery from images list
