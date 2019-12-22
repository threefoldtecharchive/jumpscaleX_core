# Threegit Tool

## Intro

3git is a tool which allows us work with data and wiki pages stored in git repositories.

## How it works

- It depends on refernces from git commits and saves it in `.3gitconfig.toml` at the root of the repo so in the next time of loading it knows the last reference where files have been processed

- This could be done through git log tool, that way we know the new files since last scan. check [here](https://github.com/threefoldtech/jumpscaleX_core/blob/development/JumpscaleCore/clients/git/GitClient.py#L219)

## usage examples

```python
# Take a jsx client
# name: is the name of the wiki / docsite
# path_source: source of the files of docsite / wiki
# path_dest: the out put destination for the processed files
test_wiki = j.tools.threegit.get(name="test_wiki", path_source="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/docs/wikis/examples/docs/", path_dest="/test/test2")
```

```python
# Then execute process with this configuration
# paran: check: revisit the repo's files according latest ref to find out new changes
# param: reset: deletes everything and rewrite the processed files
test_wiki.process(check=True)
```
