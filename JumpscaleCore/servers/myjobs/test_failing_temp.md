
in 1 console run

"""
kosmos -p "j.servers.myjobs.start(debug=True)"
"""

kosmos -p is important means we run with monkey patching on

in other console

"""
kosmos -p "j.servers.myjobs.test3(start=False,count=10)"
"""

the test3 should use the worker which runs in foreground easier to debug

experiment with count to see if the mainloop spawns more or less workers when needed.


