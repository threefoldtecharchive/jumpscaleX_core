<script>
  export let searchText;
</script>

<!--[Filters]-->
<div class="row m-5">
  <div class="col-sm-12">
    <div class="d-flex justify-content-start">
      <!--[Search]-->
      <div class="mx-4 search-width">
        <input
          type="search"
          class="form-control"
          id="InputSearch"
          placeholder="Search text"
          bind:value={searchText} />

      </div>
      <!--[Services]-->
      <!-- content here -->
      <div class="dropdown mx-2">
        <button
          class="btn btn-light dropdown-toggle pointer"
          type="button"
          id="dropdownMenuButton"
          data-toggle="dropdown"
          aria-haspopup="true"
          aria-expanded="false"
          disabled={servicesLoading}>
          Services
        </button>
        {#if services && services.length > 0}
          <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
            {#each services as service}
              <!-- content here -->
              <a
                class="dropdown-item"
                href="#"
                on:click={() => updateFilters(service, currentFilters.messageType, currentFilters.status)}>
                {service}
              </a>
            {/each}
          </div>
        {/if}
      </div>
      <!--[Message-Type]-->
      <div class="dropdown mx-2">
        <button
          class="btn btn-light dropdown-toggle pointer"
          type="button"
          id="dropdownMenuButton"
          data-toggle="dropdown"
          aria-haspopup="true"
          aria-expanded="false"
          disabled={servicesLoading}>
          Message type
        </button>
        <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
          <a
            class="dropdown-item"
            href="#"
            on:click={() => updateFilters(currentFilters.service, messageTypes.ALL, currentFilters.status)}>
            All
          </a>
          <a
            class="dropdown-item"
            href="#"
            on:click={() => updateFilters(currentFilters.service, messageTypes.ERROR, currentFilters.status)}>
            Error
          </a>
          <a
            class="dropdown-item"
            href="#"
            on:click={() => updateFilters(currentFilters.service, messageTypes.INFORMATION, currentFilters.status)}>
            Information
          </a>
          <a
            class="dropdown-item"
            href="#"
            on:click={() => updateFilters(currentFilters.service, messageTypes.WARNING, currentFilters.status)}>
            Warning
          </a>

        </div>
      </div>
      <!--[Status]-->
      <div class="dropdown mx-2">
        <button
          class="btn btn-light dropdown-toggle pointer"
          type="button"
          id="dropdownMenuButton"
          data-toggle="dropdown"
          aria-haspopup="true"
          aria-expanded="false"
          disabled={servicesLoading}>
          Status
        </button>
        <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
          <a
            class="dropdown-item"
            href="#"
            on:click={() => updateFilters(currentFilters.service, currentFilters.messageType, status.ALL)}>
            All
          </a>
          <a
            class="dropdown-item"
            href="#"
            on:click={() => updateFilters(currentFilters.service, currentFilters.messageType, status.NEW)}>
            New
          </a>
          <a
            class="dropdown-item"
            href="#"
            on:click={() => updateFilters(currentFilters.service, currentFilters.messageType, status.OPEN)}>
            Open
          </a>
          <a
            class="dropdown-item"
            href="#"
            on:click={() => updateFilters(currentFilters.service, currentFilters.messageType, status.CLOSED)}>
            Closed
          </a>

        </div>
      </div>

      <!--[Reset-Filter]-->
      <div class="mx-2">
        <button
          type="button"
          class="btn btn-light pointer"
          on:click={() => resetFilters()}
          disabled={servicesLoading}>
          Reset Filters
        </button>
      </div>
      <!--[Delete-Alerts]-->
      <div class="mx-2">
        <button
          type="button"
          class="btn btn-light pointer"
          on:click={() => deleteAllAlerts()}
          disabled={servicesLoading}>
          Delete Alerts
        </button>
      </div>
    </div>
  </div>
</div>
