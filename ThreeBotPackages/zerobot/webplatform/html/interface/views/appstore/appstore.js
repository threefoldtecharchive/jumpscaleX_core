
module.exports = {
  name: 'appstore',
  components: {},
  props: [],
  data () {
    return {
      selectedApp: null
    }
  },
  computed: {
    ...window.vuex.mapGetters([
      'apps'
    ])
  },
  mutations: {

  },
  mounted () {
    this.getVueApps()
  },
  methods: {
    ...window.vuex.mapActions([
      'installApp',
      'getVueApps',
      'uninstallApp'
    ]),
    closeDialog (save) {
      if (save) {
        if (this.selectedApp.installed) {
          this.uninstallApp(this.selectedApp)
        } else {
          this.installApp(this.selectedApp)
        }
      }
      this.selectedApp = null
    }
  }
}
