/* eslint no-undef: 0 */
/* eslint-disable no-new */
import config from '../config/index.js'

export default ({
  getInstalledPackages () {

    const frontendPackages = axios.post(`${config.jsApiUrl}package_manager/packages_list`, {
      args: {
        frontend: true
      }
    })
    return frontendPackages
  },
  checkPathForFile (path) {
    return axios.get(path)
  },
  installApp (app) {
    console.log("installing app: ", app)

    return axios.post(`${config.jsApiUrl}package_manager/package_add`, {
      args: {
        git_url: app.repository
      }
    })
  },
  uninstallApp (app) {
    return axios.post(`${config.jsApiUrl}package_manager/package_delete`, {
      args: {
        name: app
      }
    })
  }
})
