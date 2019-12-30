/* eslint no-undef: 0 */
/* eslint-disable no-new */
module.exports = {
  name: 'app',
  components: {},
  props: [],
  data() {
    return {
      showDialog: false,
      showBadge: true,
      menu: false,
      alreadyAddedStores: []
    }
  },
  computed: {
    ...window.vuex.mapGetters([
      'apps',
      'currentRoom',
      'account',
      'routes'
    ]),
    topRoutes() {
      return this.routes.filter(r => r.meta.position === 'top')
    },
    bottomRoutes() {
      return this.routes.filter(r => r.meta.position === 'bottom')
    },
    bottomNavApps() {
      return this.topRoutes.concat(this.bottomRoutes)
    },
    showOverlay() {
      var hasApps = this.apps && !!this.apps.length
      var isLoading = false
      return !hasApps && isLoading
    }
  },
  mounted() {
    this.getApps()
  },
  methods: {
    ...window.vuex.mapActions([
      'getApps',
      'logout',
      'clearCurrentRoom',
      'addRoute'
    ]),
    signOut() {
      this.logout()
      this.$router.push({
        name: 'login'
      })
    },
    getAllRoutes(app) {
      return app.routes.map(route => {
        return {
          path: `/${app.name.toLowerCase()}${route.path}`,
          component: httpVueLoader(`/${app.name}/${route.component}`),
          name: `${app.name.toLowerCase()}${route.name ? '-' + route.name : ''}`,
          meta: {
            ...route.meta,
            app: true,
            position: route.meta.position ? route.meta.position : 'top'
          }
        }
      })
    },
    async readUrl(url) {
      return (await fetch(url)).text()
    }
  },
  watch: {
    apps(val) {
      for (let appIndex = 0; appIndex < val.length; appIndex++) {
        const app = val[appIndex]
        const storeName = `${app.name.toLowerCase()}Store`

        if (!this.alreadyAddedStores.some(x => x === storeName)) {
          this.alreadyAddedStores.push(storeName)

          import(app.store).then((store) => {
            this.$store.registerModule(storeName, store)
            this.getAllRoutes(app).forEach(route => {
              if (!this.routes.some(r => r.name === route.name)) {
                this.addRoute(route)
                this.$router.addRoutes([route])
              }
            })
          })

        }
      }
    }
  }
}
