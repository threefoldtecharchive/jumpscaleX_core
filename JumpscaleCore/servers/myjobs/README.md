# myjobs

## entities

### Job
Job represents a runnable `action` or `task` that needs to be executed `asynchronously` 

```toml
@url = jumpscale.myjobs.job
category*= ""
time_start* = 0 (T)
time_stop = 0 (T)
state* = ""
timeout = 0
action_id* = 0
args = ""   #json
kwargs = "" #json
result = "" #json
error = ""
return_queues = (LS)
```

- category: Mostly (`W` for a `worker` or `J` for a Job) used when pushed to the datachanges queue.
- time_start: when the job it started
- time_stop: when the job stopped
- state: state of the job (`OK`, `ERROR`)
- action_id: reference to python `function` stored in `action` model.
- args: list of arguments to invoke `action` with (serialized as json)
- kwargs: list of kwargs to invoke `action` with (serialized as json)
- result: result of invoking `action` with `args` and `kwargs` as json
- error: error stacktrace
- return queues: list of queues to push the results to

### Action

Action is a serialized python function `(function name, function code)` identified by a `hash` that can be referenced in multiple jobs instead of copying it over to every job.
```toml
@url = jumpscale.myjobs.action
key* = ""  #hash
code = ""
methodname = ""
```


### Worker
responsible for pulling `jobs` or `tasks` from the tasks queue and pushing results to results queue

#### Worker schema
```toml
@url = jumpscale.myjobs.worker
timeout = 3600
time_start = 0 (T)
last_update = 0 (T) 
current_job = (I)
halt = false (B)
running = false (B)
pid = 0
```
- timeout: when to timeout the executing job
- time_start: when the worker started
- last_update: when it was last updated?  (FIXME)
- current_job: the current job the worker is processing
- halt:  worker halted
- running: is worker running atm
- pid: process id of the worker.


## Design

`myjobs` manages workers to execute `async` tasks. meaning it keeps track of the workers maybe in a dict `self.workers`


### Number of workers
can be controlled using `workers_nr_max` (should be defaulted to `cpu_count`) and `workers_nr_min` 

#### Workers internals
Getting a new worker is done using `myworker(id=999999, onetime=False, showout=False)`
- onetime: asks the worker to execute only one time (and to run the job only 1 time even if it failed)
- showout for debugging purposes.

##### Worker loop
- getting a `job id` from work queue `queue`
- if there's a `job` object in the database
    - we get the referenced `action` using `action_id` in job model
    - we `exec` the `action` code and get a reference to the action method using `eval`
    - we get the `args` and `kwargs` saved on the job model
    - we invoke the action method on `args` and `kwargs` 
        - if execution was ok we update the `job.result` and state to `OK`
        - if there was an exception we update `job.error` with the stacktrace and state to `ERROR`

- if the worker as invoked with `onetime` param tham it will execute the worker loop only once.

### Loops
 with two loops 
- mainloop: this one creates subprocesses for workers automatically (and decrease) only relevant if not workers started in e.g. tmux
- dataloop: gets the return objects from workers (redis queues) and processes them towards the BCBD

#### mainloop



#### dataloop



### Queues

`myjobs` has two queues
- queue: 
- queue_data:

#### queue


#### queue_data
