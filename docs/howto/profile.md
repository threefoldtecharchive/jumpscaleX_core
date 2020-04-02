# Using profilers

## Integrated (recommended)

To start profiling using JSX you can use the following available methods:

```python
pr = j.core.profileStart()
#do stuff
j.core.profileStop(pr)
```

## Alternatives (more complex)

JSX doesn't allow for better visualization in that case it is better to use other tools.

### graphical

#### OSX preparation 

```bash
brew install graphviz
brew install qcachegrind --with-graphviz
pip3 install pyprof2calltree
```

```bash
rm /tmp/prof.out
python3 -m cProfile -o /tmp/prof.out /usr/local/bin/js_shell 'print(1)'
pyprof2calltree -i /tmp/prof.out -k
```

### Non graphical

```bash
pip3 install pyinstrument
```

```bash
rm /tmp/prof.out
python3 -m pyinstrument /usr/local/bin/js_shell 'print(1)'

```

