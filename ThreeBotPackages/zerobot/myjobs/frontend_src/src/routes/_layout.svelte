<script>
  import Navigation from "../components/Navigation.svelte";

  export let segment;
</script>

<style>
  /* main {
    position: relative;
    max-width: 56em;
    background-color: white;
    padding: 2em;
    margin: 0 auto;
    box-sizing: border-box;
  } */
</style>

<svelte:head>
  <title>Myjobs Visualizer</title>
</svelte:head>

<Navigation {segment} />

<main>
  <div class="container-fluid">
    <div class="row">
      <div class="col">
        <slot />
      </div>
    </div>
  </div>
</main>
