<script>
  export let task;
  export let index;
</script>

<style>
  .text-wrap {
    overflow-wrap: break-word;
  }
  .job-modal {
    max-width: 70%;
  }
</style>

<div
  class="modal fade"
  id="modal{index}"
  tabindex="-1"
  role="dialog"
  aria-labelledby="exampleModalLabel"
  aria-hidden="true">
  <div class="modal-dialog job-modal" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="exampleModalLabel">Job Details</h5>
        <button
          type="button"
          class="close"
          data-dismiss="modal"
          aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
        <!--[Data-Listing]-->
        <ul class="list-group">
          <li class="list-group-item">
            <b>Category :</b>
            {task.category}
          </li>
          <li class="list-group-item">
            <b>Time Start :</b>
            {task.time_start}
          </li>
          <li class="list-group-item">
            <b>Time Stop :</b>
            {task.time_stop}
          </li>
          <li class="list-group-item">
            <b>State :</b>
            {task.state}
          </li>
          <li class="list-group-item">
            <b>Timeout :</b>
            {task.timeout}
          </li>
          <li class="list-group-item">
            <b>Action Id :</b>
            {task.action_id}
          </li>
          <li class="list-group-item">
            <b>Kwargs :</b>
            {task.kwargs}
          </li>
          <li class="list-group-item">
            <b>Result :</b>
            {task.result}
          </li>
          <li class="list-group-item">
            <b>Error :</b>
            <p class="text-wrap">{task.error}</p>
          </li>
        </ul>

      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">
          Close
        </button>
      </div>
    </div>
  </div>
</div>
