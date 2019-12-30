

## includes 1

### using custom link and a pattern
needs to walk over all files in threefoldtech:jumpscaleX_core till it finds 'schemas/readme.md' in path
if more than 1 then error
needs to cache this for 1h (like check of links, also there caching of 1h)

!!!include("threefoldtech:home:projects/readme.md")

## includes 2

!!!include("threefoldtech:home(master):projects/readme.md")

## includes 3

!!!include("threefoldtech:home:book.json")

### guessing code block type from file
if json or yaml or toml, py, js,...etc, then put in codeblock


!!!include("threefoldtech:jumpscaleX_libs(development):macros/dot.py")

## includes 4

### without extension
when no extension checks for .md
when no account or repo then is current repo


!!!include("small")

### with extension
!!!include("small.md")

## includes 5

### from current docsite account/repo...
when no extension checks for .md
when no account or repo then is current repo


!!!include("home:networks")

## include long

### custom link from a different hosting service
!!!include("threefoldforks:Threefold-Circles-back:CODE_OF_CONDUCT.md", host="gitlab.com")

### or using the full url

#### full url
js file
!!!include("https://gitlab.com/threefoldforks/Threefold-Circles-events/blob/master/gulpfile.js")

markdown document

!!!include("https://gitlab.com/threefoldforks/Threefold-Circles-events/blob/master/README.md")

raw link (auto detected)

!!!include("https://gitlab.com/threefoldforks/Threefold-Circles-back/raw/master/CODE_OF_CONDUCT.md")


#### raw urls
when https and : inside then it means it needs to be a git repo (can be gitlabs or gogs too) so the code will be checked out and fhe file looked for
when https and raw=True: then its a real link which can be downloaded with curl


!!!include("https://gitlab.com/threefoldforks/Threefold-Circles-back/raw/master/CODE_OF_CONDUCT.md", raw=True)
