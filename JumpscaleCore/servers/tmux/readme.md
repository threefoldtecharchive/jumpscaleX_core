
## info

- http://blog.isaachodes.io/p/tmux-simply-explained/

## terms

### session

is a tmux process

### window

is a tab inside the session (what you can go inbetween)

### pane

is a split inside the window

## commands

list the sessions

```
tmux ls
```

connect to a tmux process (session)

```bash
tmux attach -t mysession
```

some shortcuts

- ctrl-b 0: go to window 0 (first one)
- ctrl-b : new-window
- ctrl-0: go to first window

## jumpscale example

```python
#when only 1 pane no need to specify
j.servers.tmux.execute(cmd="ls /", session='main', window='main')
```
