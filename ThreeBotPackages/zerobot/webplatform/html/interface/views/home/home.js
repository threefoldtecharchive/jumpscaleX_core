
module.exports = {
  name: 'home',
  components: {},
  props: [],
  data () {
    return {

    }
  },
  computed: {
    ...window.vuex.mapGetters([
      'routes'
    ])
  },
  async mounted () {
    // Check init
    var initiazationData = await window.initializeService.getInitializationData()
    if (initiazationData.data.users.length === 0) {
      // Redirect to initialize
      this.$router.push({ name: 'initialize' })
    }
  },
  methods: {
  }
}
