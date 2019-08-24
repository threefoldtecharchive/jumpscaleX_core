## Docsite

A docsite is a collection of markdown documents.
This tool will process the markdown documents and will keep the docs in memory.

There is also a macro system involved which allows the markdown documents to be easily pre-processed before being used.

### to test

do
```bash
kosmos 'j.tools.markdowndocs.test()'
```

### the test code

```python

url = "https://github.com/threefoldtech/jumpscale_weblibs/tree/master/docsites_examples/test/"
ds = self.load(url,name="test")

doc = ds.doc_get("links")

#data comes from directories above
assert doc.data == {'color': 'green', 'importance': 'high', 'somelist': ['a', 'b', 'c']}

print (doc.images)

for link  in doc.links:
    print(link)

assert str(doc.link_get(cat="image",nr=0)) == 'link:image:unsplash.jpeg'
assert str(doc.link_get(cat="link",nr=0)) == 'link:link:https://unsplash.com/'

doc = ds.doc_get("include_test")

doc = ds.doc_get("use_data")
md = str(doc.markdown)
assert "- a" in md
assert "- b" in md
assert "high" in md

doc = ds.doc_get("has_data") #combines data from subdirs as well as data from doc itself

assert doc.data == {'color': 'blue',
                 'colors': ['blue', 'red'],
                 'importance': 'somewhat',
                 'somelist': ['a', 'b', 'c']}


print ("test of docsite done")


```
