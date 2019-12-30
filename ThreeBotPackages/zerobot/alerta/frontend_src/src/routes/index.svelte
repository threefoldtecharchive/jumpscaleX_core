<script>
  import Alerts from "../components/Alerts.svelte";
  import Spinner from "../components/Spinner.svelte";
  import { getAlerts, deleteAll } from "./data";
  import { formatDate } from "./common";
  import { onMount } from "svelte";

  let alerts;
  let searchText = "";
  let formattedAlerts = "";
  let currentFilteredAlerts;
  let isAlertsLoaded = false;
  let servicesLoading = true;
  let isAllAlertsDeleted = false;
  const environments = [
    { id: "all", name: "All", selected: true },
    { id: "production", name: "Production", selected: false },
    { id: "staging", name: "Staging", selected: false },
    { id: "development", name: "Development", selected: false },
    { id: "infrastructure", name: "Infrastucture", selected: false }
  ];

  let services;
  const severity = {
    ALL: "ALL",
    50: "CRITICAL",
    40: "ERROR",
    30: "WARNING",
    15: "STDOUT",
    10: "DEBUG"
  };
  const messageTypes = {
    ALL: "ALL",
    ERROR: "ERROR",
    INFORMATION: "INFORMATION",
    WARNING: "WARNING"
  };
  const status = { ALL: "ALL", OPEN: "OPEN", CLOSED: "CLOSED", NEW: "NEW" };
  let currentFilters = {
    service: "ALL",
    messageType: messageTypes.ALL,
    status: status.ALL
  };

  onMount(async () => {
    updateAlerts("all");
  });

  //Get Data from the API
  function updateAlerts(environment) {
    isAlertsLoaded = false;
    isAllAlertsDeleted = false; //The alerts all available now and not deleted (reintialize the state)
    alerts = [];

    getAlerts(environment)
      .then(response => {
        // handle success
        let parsedJson = response.data.result;
        alerts = parsedJson.alerts;
        formattedAlerts = convertData(parsedJson.alerts);
        filterAlerts(formattedAlerts);
        getServices();
        isAlertsLoaded = true;
      })
      .catch(err => {
        throw err;
        console.log("error ", err);
      });
  }

  function updateFilters(selectedService, selectedMessageType, selectedState) {
    currentFilters = {
      service: selectedService,
      messageType: selectedMessageType,
      status: selectedState
    };
    filterAlerts(formattedAlerts);
  }

  function convertData(alerts) {
    for (let i = 0; i < alerts.length; i++) {
      let alert = alerts[i];

      alert.service = alert.service.toUpperCase();
      alert.status = alert.status.toUpperCase();
      alert.messageType = alert.messageType.toUpperCase();
      alert.severity = severity[alert.severity];
      alert.time = formatDate(alert.time);
    }
    return alerts;
  }

  function filterAlerts(filteredAlerts) {
    if (currentFilters.service != "ALL")
      filteredAlerts = filteredAlerts.filter(singelAlert => {
        return singelAlert.service == currentFilters.service;
      });
    if (currentFilters.messageType != messageTypes.ALL)
      filteredAlerts = filteredAlerts.filter(singelAlert => {
        return singelAlert.messageType == currentFilters.messageType;
      });
    if (currentFilters.status != status.ALL)
      filteredAlerts = filteredAlerts.filter(singelAlert => {
        return singelAlert.status == currentFilters.status;
      });
    currentFilteredAlerts = filteredAlerts; //keeping the current filtered alerts
    alerts = filteredAlerts; //update the alerts to update the Rendering
  }

  $: if (searchText) {
    searchAlertsText();
  }
  function searchAlertsText() {
    alerts = currentFilteredAlerts.filter(singleAlert => {
      return singleAlert.text.includes(searchText);
    });
  }
  function resetFilters() {
    currentFilters = {
      service: "ALL",
      messageType: messageTypes.ALL,
      status: status.ALL
    };
    document.getElementById("InputSearch").value = "";
    filterAlerts(formattedAlerts);
  }
  function getServices() {
    servicesLoading = true;
    services = formattedAlerts.map(singleAlert => singleAlert.service);
    services = Array.from([...new Set(services)]); //Making services unique and convert it from set to array
    services.unshift("ALL"); //Add "All" in the begining of the array
    servicesLoading = false;
  }

  function deleteAllAlerts() {
    deleteAll()
      .then(res => {
        alerts = [];
        isAllAlertsDeleted = true;
      })
      .catch(err => {
        console.log("error while deleting all alerts", err);
      });
  }
</script>

<style>
  .search-width {
    width: 350px;
  }
</style>

<svelte:head>
  <title>Alerta</title>
</svelte:head>

<!--[Container]-->
<div class="container-fluid">
  <!--[Title]-->
  <div class="m-3 text-center">
    <h1>Central Alert System</h1>
  </div>
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
  <!--[Tabs]-->
  <div class="row mt-4">
    <div class="col-sm-12 ml-4">
      <div>
        <ul class="nav nav-pills mb-3" id="pills-tab" role="tablist">
          {#each environments as item}
            <li class="nav-item">
              <a
                class="nav-link {item.selected ? 'active' : ''}"
                id="pills-{item.id}-tab"
                data-toggle="pill"
                href="#pills-{item.id}"
                role="tab"
                aria-controls="pills-{item.id}"
                aria-selected={item.selected ? 'true' : ''}
                on:click={() => updateAlerts(item.id)}>
                {item.name}
              </a>
            </li>
          {/each}
        </ul>
        <div class="tab-content" id="pills-tabContent">
          {#each environments as item}
            <div
              class="tab-pane fade show active"
              id="pills-{item.id}"
              role="tabpanel"
              aria-labelledby="pills-{item.id}-tab" />
          {/each}
        </div>
      </div>

    </div>
  </div>
  <!--[Alerts]-->
  {#if alerts && alerts != '' && isAlertsLoaded && !isAllAlertsDeleted}
    <!-- content here -->
    <div class="row">
      <div class="col-sm-12">
        <Alerts {alerts} />
      </div>
    </div>
  {:else if !isAlertsLoaded && !isAllAlertsDeleted}
    <Spinner />
  {:else if isAlertsLoaded && isAllAlertsDeleted}
    <div class="mt-5 text-center">
      <h2>All the alerts have been deleted.</h2>
    </div>
  {:else}
    <div class="mt-5 text-center">
      <h2>There is no alerts matching your criteria</h2>
    </div>
  {/if}
</div>
