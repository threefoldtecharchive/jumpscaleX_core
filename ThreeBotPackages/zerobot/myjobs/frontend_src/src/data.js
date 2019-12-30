import axios from "axios";


export function getJobs() {
    return axios.get("/zerobot/myjobs_ui/actors/myjobs/list_jobs");
}

export function getWorkers() {
    return axios.get("/zerobot/myjobs_ui/actors/myjobs/list_workers");
}
