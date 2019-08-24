## same repo

### modify headers

!!!include("threefoldtech:jumpscaleX(development):test_src.md", header_levels_modify=2)

### docstrings

!!!include("threefoldtech:jumpscaleX(development):test.py", doc_only=True)

### skip remarks (lines start with hash)
!!!include("threefoldtech:jumpscaleX(development):test.py", remarks_skip=True)

### get only part A
!!!include("threefoldtech:jumpscaleX(development):test_src.md!A")


## external repo

!!!include("abom:test_custom_md:test_src.md!A")

!!!include("https://github.com/abom/test_custom_md/tree/master/docs/test_src.md")


## Including full directory using ` includes`

!!!includes("testat")

## using include_original with a page from specific docsite

!!!include_original(name="testat/a", docsite="tokens")

## using include_original for a python file, and repo
!!!include_original(repo="https://github.com/Hamdy/test_custom_md/blob/master/docs", name="test.py")

## using include_original to include certain part of page
!!!include_original(name="testat/a", docsite="tokens", start="-", end="man")

## using include to include file test.py
!!!include(link="test.py", codeblock_type='python')
