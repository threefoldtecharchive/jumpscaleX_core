<script>
  import { getWorkers } from "../data";
  import { formatDate } from "../common";
  import Spinner from "./Spinner.svelte";
  import { onMount } from "svelte";

  const state = {
    RESULT: "OK",
    ERROR: "ERROR",
    NEW: "NEW",
    HALTED: "HALTED",
    WAITING: "WAITING",
    ALL: "all"
  };
  let isAllWorkersAvailable = false;
  let counters = {
    success: 0,
    error: 0,
    new: 0,
    halted: 0,
    waiting: 0,
  };

  let currentFilter = state.ALL;
  let workers = [];

  onMount(async () => {
    isAllWorkersAvailable = false;
    getWorkers()
      .then(function(data) {
        if (!data) {
          return;
        }
        isAllWorkersAvailable = true;
        workers = data.data.workers;
        workers.forEach(worker => {
          worker.state = worker.state.toUpperCase();
          if (worker.error) {
            worker.error = JSON.stringify(worker.error);
          }

          worker.time_start = formatDate(worker.time_start);
          worker.last_update = formatDate(worker.last_update);
        });

        //Calculating the statstics relatedt to the workers
        statsticsCalculation();
      })
      .catch(err => {
        console.log(err);
      });
  });

  function statsticsCalculation() {
    workers.forEach(worker => {
      if (worker.state == state.RESULT) counters["success"]++;
      else if (worker.state == state.ERROR) counters["error"]++;
      else if (worker.state == state.NEW) counters["new"]++;
      else if (worker.state == state.HALTED) counters["halted"]++;
      else if (worker.state == state.WAITING) counters["waiting"]++;
      else {
      }
    });
  }
  $: filteredWorkers = () => {
    counters = {
      success: 0,
      error: 0,
      new: 0,
      halted: 0,
      waiting: 0
    };
    statsticsCalculation();
    if (currentFilter == state.ALL) return workers;
    else if (currentFilter == state.RESULT)
      return WorkersFiltering(state.RESULT);
    else if (currentFilter == state.ERROR) return WorkersFiltering(state.ERROR);
    else if (currentFilter == state.NEW) return WorkersFiltering(state.NEW);
    else if (currentFilter == state.HALTED)
      return WorkersFiltering(state.HALTED);
    else if (currentFilter == state.WAITING)
      return WorkersFiltering(state.WAITING);
  };

  function updateFilter(filter) {
    currentFilter = filter;
  }
  function WorkersFiltering(state) {
    let filteredWorkers = [];
    workers.forEach(worker => {
      if (worker.state == state) filteredWorkers.push(worker);
    });
    return filteredWorkers;
  }
</script>

<style>
  .mt-3 {
    margin-top: 20px;
  }
</style>

<!--[Header]-->
<h1>Workers</h1>
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
      on:click={() => updateFilter(state.NEW)}
      class:active={currentFilter === state.NEW}>
      New
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
      on:click={() => updateFilter(state.HALTED)}
      class:active={currentFilter === state.HALTED}>
      Halted
    </button>
  </div>

  <div class="mr-3">
    <button
      class="btn"
      on:click={() => updateFilter(state.WAITING)}
      class:active={currentFilter === state.WAITING}>
      Waiting
    </button>
  </div>
</div>

<!--[Statstics]-->
<div class="row mt-5">

  <div class="col-sm-12">
    <table class="table table-striped">
      <thead>
        <tr>
          <th class="text-center" scope="col">Total</th>
          <th class="text-center" scope="col">New</th>
          <th class="text-center" scope="col">Success</th>
          <th class="text-center" scope="col">Failure</th>
          <th class="text-center" scope="col">Halted</th>
          <th class="text-center" scope="col">Waiting</th>
        </tr>
      </thead>
      <tbody class="text-center">
        <td>{workers.length}</td>
        <td>{counters['new']}</td>
        <td>{counters['success']}</td>
        <td>{counters['error']}</td>
        <td>{counters['halted']}</td>
        <td>{counters['waiting']}</td>
      </tbody>
    </table>
  </div>
</div>

{#if filteredWorkers() && filteredWorkers().length > 0 && isAllWorkersAvailable}
  <!--[Containder]-->
  <div>
    <div class="row mt-5">
      <!--[Workers-Data]-->
      <div class="col-sm-12">
        <table class="table table-striped">
          <!--[Workers-Data-Headers]-->
          <thead>
            <tr>
              <!-- <th scope="col">#</th> -->
              <th scope="col">#</th>
              <th scope="col">State</th>
              <th scope="col">Halt</th>
              <th scope="col">Pid</th>
              <th scope="col">Current Job</th>
              <th scope="col">Last Update</th>
              <th scope="col">Time Start</th>
              <th scope="col">Timeout</th>
              <th scope="col">Type</th>
              <th scope="col">Error</th>

            </tr>
          </thead>
          <!--[Workers-Data-Body]-->
          <tbody>
            {#each workers as worker, i}
              <tr>
                <!-- <th scope="row">{i + 1}</th> -->
                <td>{worker.id}</td>

                {#if worker.state == state.RESULT}
                  <td>
                    <span class="badge badge-success">{worker.state}</span>
                  </td>
                {:else if worker.state == state.ERROR}
                  <td>
                    <span class="badge badge-danger">{worker.state}</span>
                  </td>
                {:else if worker.state == state.NEW}
                  <td>
                    <span class="badge badge-primary">{worker.state}</span>
                  </td>
                {:else if worker.state == state.HALTED}
                  <td>
                    <span class="badge badge-secondary">{worker.state}</span>
                  </td>
                {:else if worker.state == state.WAITING}
                  <td>
                    <span class="badge badge-dark">{worker.state}</span>
                  </td>
                {:else}
                  <td>
                    <span class="badge badge-warning">{worker.state}</span>
                  </td>
                {/if}
                <td>{worker.halt}</td>
                <td>{worker.pid}</td>
                {#if worker.current_job == 2147483647}
                    <td>N/A</td>
                {:else}
                    <td>{worker.current_job}</td>
                {/if}
                <td>{worker.last_update}</td>
                <td>{worker.time_start}</td>
                <td>{worker.timeout}</td>
                <td>{worker.type}</td>
                <td>{worker.error}</td>

              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

  </div>
{:else if filteredWorkers().length == 0 && isAllWorkersAvailable}
  <div>
    <h2>There is no Workers matching your criteria</h2>
  </div>
{:else if !isAllWorkersAvailable}
  <Spinner />
{/if}
