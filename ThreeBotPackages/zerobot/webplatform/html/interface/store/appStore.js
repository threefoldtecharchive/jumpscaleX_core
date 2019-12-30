import appService from '../services/appServices.js'
export default ({
  state: {
    apps: []
  },
  actions: {
    getApps: (context) => {
      var tmpApps = []

      context.dispatch('wait/start', 'getApps', {
        root: true
      })

      appService.getVueApps().then(response => {
        context.dispatch('wait/end', 'getApps', {
          root: true
        })

        response.data.packages.forEach(function (item, index) {
          appService.checkPathForFile(`${window.location.origin}/${item.name}/router.json`).then(r => {
            if (r.status === 200) {
              item.routes = r.data
              item.store = `/${item.name}/store.js`
            }
            tmpApps.push(item)
          })
        })
      }).catch(e => {
        context.dispatch('wait/end', 'getApps', {
          root: true
        })
      })

      context.commit('setApps', tmpApps)
    },
    installApp: (context, app) => {
      context.dispatch('wait/start', 'installApp', {
        root: true
      })
      appService.installApp(app).then(response => {
        context.dispatch('wait/end', 'installApp', {
          root: true
        })
        context.dispatch('getApps')
      })
    },
    uninstallApp: (context, app) => {
      context.dispatch('wait/start', 'uninstallApp', {
        root: true
      })
      appService.uninstallApp(app).then(response => {
        context.dispatch('wait/end', 'uninstallApp', {
          root: true
        })
        context.dispatch('getApps')
      })
    }
  },
  mutations: {
    setApps: (state, app) => {
      state.apps = app
    },
    updateApp: (state, app) => {
      state.apps.find(x => x.name === app.name).installed = app.installed
    }
  },
  getters: {
    apps: (state) => state.apps
  }
})
