from uuid import uuid4
from Jumpscale import j
from Jumpscale.tools.threegit.macros import include

import pytest

markdowndocs_client = j.tools.threegit
doc = markdowndocs_client.load(
    "https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/zerobot/wiki_examples/wiki",
    name="test",
    pull=False,
)
test_doc = doc.doc_get("test")


def test_include_from_repo(doc=test_doc):
    data = include.include(doc=test_doc, link="test_src.md")
    assert "This is a paragraph !!A!!" in data


def test_include_part_with_marker(doc=test_doc):
    data = include.include(doc=test_doc, link="test_src.md!A")
    assert "This is a paragraph \nYou need to include this para, para, para" in data
    assert "!!A!!" not in data
    assert "!!B!!" not in data
    data = include.include(doc=test_doc, link="test_src.md!B")
    assert "A new para, \nThis is a new para" in data
    assert "This is a paragraph" not in data
    assert "!!A!!" not in data
    assert "!!B!!" not in data


def test_include_docstrings(doc=test_doc):
    data = include.include(doc=test_doc, link="test.py", doc_only=True)
    assert "method that print self" in data
    assert "A class\n    for printing" in data
    assert "nothing is here" in data
    assert "class A:" not in data
    assert "def meth(" not in data


def test_include_with_remarks_skip(doc=test_doc):
    data = include.include(doc=test_doc, link="test_src.md", remarks_skip=True)
    assert "## head" not in data


def test_include_headers_modify(doc=test_doc):
    data = include.include(doc=test_doc, link="test_src.md", header_levels_modify=-1)
    assert "# head" in data
    assert "## head" not in data


def test_include_from_other_repo(doc=test_doc):
    markdowndocs_client = j.tools.markdowndocs
    docsite = markdowndocs_client.load("https://github.com/abom/test_custom_md/tree/master", name="newdocsite")
    data = include.include(doc=test_doc, docsite_name="newdocsite", link="test_src.md")
    assert "[b](test.md)" in data
    assert "!!!dot" not in data


def test_include_custom_link(doc=test_doc):
    # test external repo with custom link
    # the same like above, but using custom links format directly (instead of loading by hand)
    data = include.include(doc=test_doc, link="abom:test_custom_md(master):docs/test_src.md")
    assert "[b](test.md)" in data
    assert "!!!dot" not in data
