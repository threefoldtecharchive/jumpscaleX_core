#!/usr/bin/env bash

export PBASE=/sandbox

export PATH=$PBASE/bin:/bin:/usr/local/bin:/usr/bin:/bin:$PATH

if [ "$(uname)" = 'Darwin' ]; then
    HOST='OSX'
else
    HOST="$(hostname)"
fi
export HOST="$HOST"

if [ -e $PBASE/bin/python3.6 ]; then
    export PYTHONPATH=$PBASE/lib/python:$PBASE/lib/pythonbin:$PBASE/lib/python.zip:$PBASE/lib/jumpscale:$PBASE/lib/pythonbin/lib-dynload:$PBASE/bin
    export LIBRARY_PATH="$PBASE/bin:$PBASE/lib"
    export LD_LIBRARY_PATH="$LIBRARY_PATH"
    export PYTHONHOME=$PBASE
    export LDFLAGS="-L$LIBRARY_PATH/"
    export PS1="3BOT:$HOST:\W: "
else
    export PYTHONPATH=$PBASE/lib/jumpscale
    unset PYTHONHOME
    export PS1="3BOTDEVEL:$HOST:\W: "
fi

export VIEWER=view

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# export HOME=$PBASE/root
# export HOMEDIR=/root

export LUALIB="/sandbox/openresty/lualib"
export LUA_PATH="?.lua;$LUALIB/?/init.lua;$LUALIB/?.lua;$LUALIB/?/?.lua;$LUALIB/?/core.lua;/sandbox/openresty/lapis/?.lua"
export LUA_CPATH="$LUALIB/?.so;./?.so"
export LAPIS_OPENRESTY=$PBASE/bin/openresty


#TERMINFO="xterm-256colors"
#export TERMINFO

LC_ALL="en_US.UTF-8"
export LC_ALL

LANG="en_US.UTF-8"
export LANG

echo "OK"
