<script>
  import TasksRendering from "./TasksRendering.svelte";
  import { getJobs } from "../data";
  import { formatDate } from "../common";
  import Spinner from "./Spinner.svelte";
  import { onMount } from "svelte";

  let allTasks = [];
  let isAllTasksAvailable = false;
  //Make all the states UpperCase
  allTasks.forEach(task => {
    task.state = task.state.toUpperCase();
  });

  onMount(async () => {
    isAllTasksAvailable = false;

    getJobs()
      .then(data => {
        isAllTasksAvailable = true;
        if (!data) {
          return;
        }
        allTasks = data.data.jobs;
        //Make all the states UpperCase
        allTasks.forEach(task => {
          task.state = task.state.toUpperCase();
          task.kwargs = JSON.stringify(task.kwargs);
          task.result = JSON.stringify(task.result);
          task.error = JSON.stringify(task.error);
          task.time_start = formatDate(task.time_start);
          task.time_stop = formatDate(task.time_stop);
        });
      })
      .catch(err => {
        console.log(err);
      });
  });
</script>

<style>

</style>

<!--[Header]-->
<h1>Jobs</h1>
{#if allTasks && allTasks.length > 0 && isAllTasksAvailable}
  <TasksRendering {allTasks} />
{:else if allTasks.length == 0 && isAllTasksAvailable}
  <div>
    <h2>There is no Jobs</h2>
  </div>
{:else if !isAllTasksAvailable}
  <Spinner />
{/if}
