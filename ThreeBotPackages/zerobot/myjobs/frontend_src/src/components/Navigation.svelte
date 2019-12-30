<script>
  export let segment;
</script>

<style>
  /* Style for "active" links; need to mark this :global because the router adds the class directly */
  :global(a.my-active) {
    color: #9d9d9d !important;
  }
</style>

<div>
  <nav class="navbar navbar-expand-lg navbar navbar-primary bg-primary">
    <a class="navbar-brand text-white" href="#">Workers and Jobs</a>
    <button
      class="navbar-toggler"
      type="button"
      data-toggle="collapse"
      data-target="#navbarText"
      aria-controls="navbarText"
      aria-expanded="false"
      aria-label="Toggle navigation">
      <span class="navbar-toggler-icon" />
    </button>
    <div class="collapse navbar-collapse" id="navbarText">
      <ul class="navbar-nav mr-auto">
        <li class="nav-item {segment === 'workers' ? 'active' : ''}">
          <a class="nav-link text-white" href="workers">
            <span>Workers</span>
            <span class="sr-only">(current)</span>
          </a>
        </li>
        <li class="nav-item {segment === 'tasks' ? 'active' : ''}">
          <a class="nav-link text-white" href="tasks">
            <span>Jobs</span>
            <span class="sr-only">(current)</span>
          </a>
        </li>
      </ul>
      <span class="navbar-text text-white">Workers and Jobs visualization</span>
    </div>
  </nav>
</div>
