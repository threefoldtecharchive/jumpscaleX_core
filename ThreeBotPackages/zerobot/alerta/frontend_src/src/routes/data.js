
import axios from 'axios'

export function getAlert(id) {
    return axios.get("/zerobot/alerta_ui/actors/alerta/get_alert", { "params": { "alert_id": id } });
}
export function getAlerts(envName = "all") {
    return (axios.get("/zerobot/alerta_ui/actors/alerta/list_alerts_by_env", { "params": { "env_name": envName } }))
}
export function deleteAll() {
    return (axios.post("/zerobot/alerta_ui/actors/alerta/delete_all_alerts"))

}
export function deleteAlert(alertId) {
    return (axios.post("/zerobot/alerta_ui/actors/alerta/delete_alert", { "args": { "alert_id": alertId } }))
}
