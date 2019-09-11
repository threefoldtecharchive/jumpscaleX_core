worker = """
@url = jumpscale.myjobs.worker
name**= ""
timeout = 3600
time_start = 0 (T)
last_update = 0 (T)
current_job = (I)
error = "" (S)
state** = "NEW,ERROR,BUSY,WAITING,HALTED" (E)
pid = 0
#if halt on True will stop
halt = false (B)
type = "tmux,subprocess,inprocess" (E)
debug = false (B)
nr = 0 (I)
"""

action = """
@url = jumpscale.myjobs.action
actorname = ""
methodname = ""
key** = ""  #hash
code = ""
"""


job = """
@url = jumpscale.myjobs.job
name** = ""
category**= ""
time_start** = 0 (T)
time_stop** = 0 (T)
state** = "NEW,ERROR,OK,RUNNING,DONE" (E)
error_cat** = "NA,TIMEOUT,CRASH,HALTED,ERROR"  (E)
timeout = 0
action_id** = 0 (I)
kwargs = (dict)
result = "" (json)
error = (dict)
die = false (B)
#will not execute this one before others done
dependencies = (LI)

"""
