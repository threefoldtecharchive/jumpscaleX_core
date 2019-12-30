<script>
  export let allTasks = [];
  export let isError = false;
  import JobModal from "./JobModal.svelte";

  const state = {
    RESULT: "OK",
    ERROR: "ERROR",
    NEW: "NEW",
    RUNNING: "RUNNING",
    HALTED: "HALTED",
    ALL: "all"
  };

  let counters = { success: 0, error: 0, new: 0, running: 0, halted: 0 };
  let currentFilter = state.ALL;
  $: filteredTasks = () => {
    //Re-intialize the counters and re-calculate the statstics
    counters = { success: 0, error: 0, new: 0, running: 0, halted: 0 };
    statsticsCalculation();
    if (currentFilter == state.ALL) return allTasks;
    else if (currentFilter == state.RESULT) return tasksFiltering(state.RESULT);
    else if (currentFilter == state.ERROR) return tasksFiltering(state.ERROR);
    else if (currentFilter == state.NEW) return tasksFiltering(state.NEW);
    else if (currentFilter == state.RUNNING)
      return tasksFiltering(state.RUNNING);
    else if (currentFilter == state.HALTED) return tasksFiltering(state.HALTED);
  };

  function tasksFiltering(state) {
    let filteredTasks = [];
    allTasks.forEach(task => {
      if (task.state == state) filteredTasks.push(task);
    });
    return filteredTasks;
  }

  //Calculating the stastics related to the tasks
  function statsticsCalculation() {
    allTasks.forEach(task => {
      if (task.state === state.RESULT) counters["success"]++;
      else if (task.state === state.ERROR) counters["error"]++;
      else if (task.state === state.NEW) counters["new"]++;
      else if (task.state === state.RUNNING) counters["running"]++;
      else if (task.state === state.HALTED) counters["halted"]++;
      else {
      }
    });
  }

  function updateFilter(filter) {
    currentFilter = filter;
  }
</script>

<style>
  .mt-3 {
    margin-top: 20px;
  }
</style>

<!--[Filter]-->
<div class="d-flex justify-content-start">
  <div class="mr-3">
    <button
      class="btn"
      on:click={() => updateFilter(state.ALL)}
      class:active={currentFilter === state.ALL}>
      All
    </button>
  </div>
  <div class="mr-3">
    <button
      class="btn"
      on:click={() => updateFilter(state.RESULT)}
      class:active={currentFilter === state.RESULT}>
      Success
    </button>
  </div>
  <div class="mr-3">
    <button
      class="btn"
      on:click={() => updateFilter(state.ERROR)}
      class:active={currentFilter === state.ERROR}>
      Failure
    </button>
  </div>
  <div class="mr-3">
    <button
      class="btn"
      on:click={() => updateFilter(state.NEW)}
      class:active={currentFilter === state.NEW}>
      New
    </button>
  </div>
  <div class="mr-3">
    <button
      class="btn"
      on:click={() => updateFilter(state.RUNNING)}
      class:active={currentFilter === state.RUNNING}>
      Running
    </button>
  </div>
  <div class="mr-3">
    <button
      class="btn"
      on:click={() => updateFilter(state.HALTED)}
      class:active={currentFilter === state.HALTED}>
      Halted
    </button>
  </div>
</div>
<!--[Statstics]-->
{#if isError != true}
  <!--[Containder]-->
  <div class="row mt-5">
    <!--[Tasks-Data]-->
    <div class="col-sm-12">
      <!-- content here -->
      <table class="table table-striped">
        <!--[Tasks-Data-Headers]-->
        <thead>
          <tr>
            <th class="text-center" scope="col">Total Tasks</th>
            <th class="text-center" scope="col">Success Tasks</th>
            <th class="text-center" scope="col">Failure Tasks</th>
            <th class="text-center" scope="col">New Tasks</th>
            <th class="text-center" scope="col">Running Tasks</th>
            <th class="text-center" scope="col">Halted Tasks</th>
          </tr>
        </thead>
        <tbody class="text-center">
          <td>{allTasks.length}</td>
          <td>{counters['success']}</td>
          <td>{counters['error']}</td>
          <td>{counters['new']}</td>
          <td>{counters['running']}</td>
          <td>{counters['halted']}</td>
        </tbody>
      </table>
    </div>
  </div>
{/if}
<!--[Tasks-Data]-->
<div>
  <div class="row mt-5">
    <!--[Tasks-Data]-->
    <div class="col-sm-12">
      {#if filteredTasks().length > 0}
        <!-- content here -->
        <table class="table table-striped">
          <!--[Tasks-Data-Headers]-->
          <thead>
            <tr>
              <th scope="col">#</th>
              <!-- <th scope="col">Id</th> -->
              <th scope="col">Category</th>
              <th scope="col">Time Start</th>
              <th scope="col">Time Stop</th>
              <th scope="col">State</th>
              <th scope="col">Timeout</th>
              <th scope="col">Action</th>
              <!-- <th scope="col">args</th> -->
              <th scope="col">kwargs</th>
              <th scope="col">Result</th>
              <th scope="col" class="text-center">Actions</th>
              <!-- <th scope="col">Return Queues</th> -->
            </tr>
          </thead>
          <!--[Tasks-Data-Body]-->
          <tbody>
            {#each filteredTasks() as task, i}
              <tr>
                <th scope="row">{i + 1}</th>
                <!-- <td>{task.id}</td> -->
                <td>{task.category}</td>
                <td>{task.time_start}</td>
                <td>{task.time_stop}</td>
                {#if task.state == state.RESULT}
                  <td>
                    <span class="badge badge-success">{task.state}</span>
                  </td>
                {:else if task.state == state.ERROR}
                  <td>
                    <span class="badge badge-danger">{task.state}</span>
                  </td>
                {:else if task.state == state.NEW}
                  <td>
                    <span class="badge badge-primary">{task.state}</span>
                  </td>
                {:else if task.state == state.RUNNING}
                  <td>
                    <span class="badge badge-warning">{task.state}</span>
                  </td>
                {:else if task.state == state.HALTED}
                  <td>
                    <span class="badge badge-info">{task.state}</span>
                  </td>
                {/if}

                <td>{task.timeout}</td>
                <td>{task.action_id}</td>
                <!-- <td>{task.args}</td> -->
                <td>{task.kwargs}</td>
                <td>{task.result}</td>
                <td class="text-center">
                  <!--[Actions]-->
                  <div>
                    <!--[Details-Job-BTN]-->
                    <div>
                      <button
                        type="button"
                        class="btn btn-warning pointer"
                        data-toggle="modal"
                        data-target="#modal{i}">
                        Details
                      </button>
                    </div>
                  </div>
                </td>
                <!--[Modal]-->
                <div>
                  <JobModal {task} index={i} />
                </div>
              </tr>
            {/each}
          </tbody>
        </table>
      {:else}
        <h3>There is no Jobs matching your criteria</h3>
      {/if}
    </div>
  </div>
</div>
