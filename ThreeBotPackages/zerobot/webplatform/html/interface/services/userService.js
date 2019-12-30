/* eslint no-undef: 0 */
/* eslint-disable no-new */
import config from '/interface/config/index.js'

export default ({
  getUserData (doubleName) {
    return axios.get(`${config.botBackend}/api/users/${doubleName}`)
  }
})
