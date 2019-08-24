

# integrated (recommended)

```python
pr = j.core.profileStart()
#do stuff
j.core.profileStop(pr)
```

# alternatives (more complex)

## graphical

### OSX preparation 

```bash
brew install graphviz
brew install qcachegrind --with-graphviz
pip3 install pyprof2calltree
```

### e.g. hju]startup example

```
rm /tmp/prof.out
python3 -m cProfile -o /tmp/prof.out /usr/local/bin/js_shell 'print(1)'
pyprof2calltree -i /tmp/prof.out -k
```

## non graphical

### OSX

```
pip3 install pyinstrument
```

### e.g. js_shell startup example

```
rm /tmp/prof.out
python3 -m pyinstrument /usr/local/bin/js_shell 'print(1)'

```

