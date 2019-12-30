<script context="module">
  // the (optional) preload function takes a
  // `{ path, params, query }` object and turns it into
  // the data we need to render the page
  export async function preload(page, session) {
    // the `slug` parameter is available because this file
    // is called [slug].svelte
    const { id } = page.params;
    return { id };
  }
</script>

<script>
  import Worker from "../../components/Worker.svelte";
  import Spinner from "../../components/Spinner.svelte";

  export let worker;

  // TODO:
  // GETWORKER
</script>

{#if worker}
  {#if worker.id}
    <Worker {worker} />
  {:else}Worker of {id} cannot be found{/if}
{:else}
  <Spinner />
{/if}
