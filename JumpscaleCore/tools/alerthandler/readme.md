
## alerthandler

the main way how errors are being dealt with
do not change the schema without consulting despiegk please

### schema of an alert

```python
0 : id = 0 (I)
1 : identifier = "" (S)               #unique identification for the alert,is hash of alert_type+message+message_pub+cat
2 : alert_type = "bug,question,event_system,event_monitor,event_operator" (E)
3 : level = 0
4 : message = ""
5 : message_pub = ""                  #optional public message
6 : cat = ""                          #a freely chosen category can be in dot notation e.g. performance.cpu.high
7: count = 0 (I)
8: status = "closed,new,open,reopen" (E)
9: time_first = (D)
10: time_last = (D)
11: support_trace = (LO) !jumpscale.alerthandler.alert.support.trace
12: events = (LO) !jumpscale.alerthandler.alert.event
10: logs = (LO) !jumpscale.alerthandler.alert.log

@url = jumpscale.alerthandler.alert.support.trace
0 : support_severity = "info,minor,normal,high,critical" (E)        #set by operator
1 : support_status = "closed,new,open,troubleshoot,ignore" (E)
2 : support_assigned = ""                                           #optional support operator who takes responsiblity
3 : support_comment = ""

#is an event of the alert
@url = jumpscale.alerthandler.alert.event
0 : threebot_name =  (S)            #threebot names, can be more than 1
1 : process_ids = (LI)              #the process id if known, can be more than one because can happen in more than 1 process
2 : code_path = ""
3 : code_line = ""
4 : code_line_nr = 0
5 : count = 0 (I)
6 : time_first = (D)
7 : time_last = (D)
8 : trace= "" (S)
9 : data = (binary)

#optional log items
#in line with threefoldtech/jumpscaleX_core/docs/Internals/logging_errorhandling/logdict.md
@url = jumpscale.alerthandler.alert.log
0 : threebot_name =  (S)            #threebot names, can be more than 1
1 : process_id = (I)                #the process id if known
2 : logs = (LO) !jumpscale.alerthandler.alert.logitem

@url = jumpscale.alerthandler.alert.logitem
0 : filepath = ""
1 : linenr = (I)
2 : message = ""
3 : level = (I)
4 : context = (S)
5 : cat = (S)
6 : data = (S)

"""

# ## log (error) levels
# - CRITICAL 	50
# - ERROR 	40
# - WARNING 	30
# - INFO 	    20
# - STDOUT 	15
# - DEBUG 	10
```
