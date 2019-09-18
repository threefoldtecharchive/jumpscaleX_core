# myjobs

## Design

`myjobs` manages workers to execute `async` tasks. meaning it keeps track of the workers in a dict `self.workers`


## Scheduling jobs

One can schedule jobs by invoking `j.servers.myjobs.schedule`.

Example:
```
def addition(a, b):
    return a + b


job = j.servers.myjobs.schedule(addition, a=1, b=2)
job.wait(die=False) # if die is passed as true excpetion will be propagated
if job.state == "OK":
    print(job.result)
else:
    print("Job failed")
```

A method needs to be self contained no globals or improts are reused from the module the method was originated in.

See the [tests](tests) for more examples.

## Workers

Workers are the processes that do the actual work. They process the scheduled jobs and execute them. When scheduling a job one needs to starts atleast one worker for the job to be processed.

### Types of Workers
####  Inprocess

This type of worker executed the jobs in the main process.

Start:
```j.servers.myjobs.worker_start()
```

#### Tmux

This type of worker executes in a seperate processed managed by `j.servers.startupcmd`, running inside a tmux window.

Start single tmux worker:
```
j.servers.myjobs.worker_tmux_start()
```
Start multiple tmux workers:
```
j.servers.myjobs.workers_tmux_start()
```

### GIPC

Gipc workers are subprocesses managed by the mainprocess. They can be configured to dynamicly scale based on the workload.

You can set the minimal amount of workers with `j.servers.myjobs._workers_gipic_nr_min` (default 1) and the maximum aount of workers with `j.servers.myjobs._workers_gipic_nr_max` (default 10).

Start gipc workers with:
```
j.servers.myjobs.workers_subprocess_start()
```

## Models

### Job
Job represents a runnable `action` or `task` that needs to be executed `asynchronously` 

```toml
@url = jumpscale.myjobs.job
category*= ""
time_start** = 0 (T)
time_stop = 0 (T)
state** = ""
timeout = 0
action_id** =  0
kwargs = "" #json
result = "" #json
error = ""
```

- category: Mostly (`W` for a `worker` or `J` for a Job) used when pushed to the datachanges queue.
- time_start: when the job it started
- time_stop: when the job stopped
- state: state of the job (`OK`, `ERROR`)
- action_id: reference to python `function` stored in `action` model.
- kwargs: list of kwargs to invoke `action` with (serialized as json)
- result: result of invoking `action` with `args` and `kwargs` as json
- error: error stacktrace

### Action

Action is a serialized python function `(function name, function code)` identified by a `hash` that can be referenced in multiple jobs instead of copying it over to every job.
```toml
@url = jumpscale.myjobs.action
actorname = ""
methodname = ""
key** = ""  #hash
code = ""
key** = ""  #hash
```


### Worker
responsible for pulling `jobs` or `tasks` from the tasks queue and pushing results to results queue

#### Worker schema
```toml
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
```
- timeout: when to timeout the executing job
- time_start: when the worker started
- last_update: when it was last updated.
- current_job: the current job the worker is processing
- state: current state of the worker
- halt:  worker is instructed to halt
- pid: process id of the worker.


#### Workers internals
Getting a new worker is done using `myworker(id=999999, onetime=False, showout=False)`
- onetime: asks the worker to execute only one time (and to run the job only 1 time even if it failed)
- showout for debugging purposes.

##### Worker loop
- getting a `job id` from work queue `queue`
- if there's a `job` object in the database
    - we get the referenced `action` using `action_id` in job model
    - we `exec` the `action` code and get a reference to the action method using `eval`
    - we get the `kwargs` saved on the job model
    - we invoke the action method with `kwargs` 
        - if execution was ok we update the `job.result` and state to `OK`
        - if there was an exception we update `job.error` with the stacktrace and state to `ERROR`

- if the worker as invoked with `onetime` param tham it will execute the worker loop only once.

Jobs and worker objects are retreived with the redis bcdb interface.
