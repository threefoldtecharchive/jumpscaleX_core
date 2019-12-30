<script>
  import { deleteAlert } from "../routes/data";
  import AlertModal from "./AlertModal.svelte";
  import { ansiUp } from "../routes/common";

  export let alerts;
  $: alerts;
  const severity = {
    CRITICAL: "CRITICAL",
    ERROR: "ERROR",
    WARNING: "WARNING",
    STDOUT: "STDOUT",
    DEBUG: "DEBUG"
  };
  function onDeleteAlert(alertId) {
    //Call gedis actor
    deleteAlert(alertId)
      .then(resp => {
        let toBeDeletedArrayIndex = getIndexOfAlert(alertId);
        alerts.splice(toBeDeletedArrayIndex, 1);
        alerts = [...alerts];
      })
      .catch(err => {
        console.log(err);
      });
  }

  function getIndexOfAlert(alertId) {
    for (let i = 0; i < alerts.length; i++) {
      if (alerts[i].id == alertId) return i;
    }
  }
</script>

<div>
  <div class="row">
    <!--[Tasks-Data]-->
    <div class="col-sm-12 _m-4">
      <!-- content here -->
      <table class="table table-striped">
        <!--[Tasks-Data-Headers]-->
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Severity</th>
            <th scope="col">Status</th>
            <th scope="col">Time</th>
            <th scope="col">Count</th>
            <th scope="col">Environment</th>
            <th scope="col">Service</th>
            <th scope="col">Resource</th>
            <th scope="col">Event</th>
            <th scope="col">Message Type</th>
            <th scope="col">Text</th>
            <!-- <th scope="col">Text</th> -->
            <th scope="col" class="text-center">Action</th>
          </tr>
        </thead>
        <!--[Tasks-Data-Body]-->
        <tbody>

          <!-- content here -->
          {#each alerts as myAlert}
            <tr>
              <th scope="row">
                <a href="/zerobot/alerta_ui/alert/{myAlert.id}">{myAlert.id}</a>
              </th>
              {#if myAlert.severity == severity.CRITICAL}
                <td>
                  <span class="badge badge-danger">{myAlert.severity}</span>
                </td>
              {:else if myAlert.severity == severity.ERROR}
                <td>
                  <span class="badge badge-info">{myAlert.severity}</span>
                </td>
              {:else if myAlert.severity == severity.WARNING}
                <td>
                  <span class="badge badge-warning">{myAlert.severity}</span>
                </td>
              {:else if myAlert.severity == severity.STDOUT}
                <td>
                  <span class="badge badge-secondary">{myAlert.severity}</span>
                </td>
              {:else}
                <td>
                  <span class="badge badge-primary">{myAlert.severity}</span>
                </td>
              {/if}
              <td>{myAlert.status}</td>
              <td>{myAlert.time}</td>
              <td>{myAlert.count}</td>
              <td>{myAlert.environment}</td>
              <td>{myAlert.service}</td>
              <td>{myAlert.resource}</td>
              <td>{myAlert.event}</td>
              <td>{myAlert.messageType}</td>
              <td>
                {@html ansiUp.ansi_to_html(myAlert.text)}
              </td>
              <td>
                <!--[Actions]-->
                <div class="d-flex d-flex justify-content-center">
                  <!--[Delete-Alert-BTN]-->
                  <div class="mr-1">
                    <button
                      type="button"
                      class="btn btn-primary pointer"
                      on:click={() => onDeleteAlert(myAlert.id)}>
                      Delete
                    </button>
                  </div>
                  <!--[Details-Alert-BTN]-->
                  <div>
                    <button
                      type="button"
                      class="btn btn-warning pointer"
                      data-toggle="modal"
                      data-target="#modal{myAlert.id}">
                      Details
                    </button>
                  </div>
                </div>
              </td>
              <!--[Modal]-->
              <div>
                <AlertModal {myAlert} index={myAlert.id} />
              </div>
            </tr>
          {/each}
        </tbody>
      </table>

    </div>
  </div>
</div>
