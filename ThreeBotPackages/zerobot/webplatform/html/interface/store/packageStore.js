import packageService from '../services/packageServices.js'

export default ({
  state: {
    packages: []
  },
  actions: {
    getInstalledPackages: async (context) => {
      var tmpPackages = []
      context.dispatch('wait/start', 'getInstalledPackages', {
        root: true
      })
      const response = await packageService.getInstalledPackages()
      for (const pkg of response.data.packages) {
        try {
          const routesResponse = await packageService.checkPathForFile(`${window.location.origin}/${pkg.name}/router.json`)
          if (response.status === 200) {
            pkg.routes = routesResponse.data
            pkg.store = `/${pkg.name}/store.js`
          }
          tmpPackages.push(pkg)
        } catch (err) {
          console.log(`Could not add frontendpackage: ${pkg.name}`)
        }
      }
      context.commit('setPackages', tmpPackages)
    },
    installApp: (context, app) => {
      context.dispatch('wait/start', 'installApp', {
        root: true
      })
      packageService.installApp(app).then(response => {
        context.dispatch('wait/end', 'installApp', {
          root: true
        })

        setTimeout(function () {
          console.log('trying to get pkgs after timeout')
          context.dispatch('getInstalledPackages')
        }, 2000)
      })
    },
    uninstallApp: (context, app) => {
      context.dispatch('wait/start', 'uninstallApp', {
        root: true
      })
      packageService.uninstallApp(app.appname.toLowerCase()).then(response => {
        context.dispatch('wait/end', 'uninstallApp', {
          root: true
        })
        setTimeout(function () {
          console.log('trying to get pkgs after timeout')
          context.dispatch('getInstalledPackages')
        }, 2000)
      })
    }
  },
  mutations: {
    setPackages: (state, pkg) => {
      console.log('setpkgs: ', pkg)
      state.packages = pkg
    },
    updatePackage: (state, pkg) => {
      state.packages.find(x => x.name === pkg.name).installed = pkg.installed
    }
  },
  getters: {
    installedPackages: (state) => state.packages
  }
})
