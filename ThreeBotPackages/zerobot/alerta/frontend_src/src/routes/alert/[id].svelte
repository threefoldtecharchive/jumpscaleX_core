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
  import AlertDetails from "../../components/AlertDetails.svelte";
  import Spinner from "../../components/Spinner.svelte";
  import { getAlert } from "../data";
  import { onMount } from "svelte";

  export let id;
  export let myAlert;

  onMount(async () => {
    getAlert(id).then(resp => {
      myAlert = resp.data;
    });
  });
</script>

{#if myAlert}
  {#if myAlert.id}
    <AlertDetails {myAlert} />
  {:else}Alert of {id} cannot be found{/if}
{:else}
  <Spinner />
{/if}
