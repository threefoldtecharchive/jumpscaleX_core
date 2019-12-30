module.exports = {
  name: 'login',
  components: {},
  props: [],
  data () {
    return {

    }
  },
  computed: {
    ...window.vuex.mapGetters([
      'loginUrl',
      'account'
    ]),
    isLoggingIn () {
      return !!this.$route.query.username
    }
  },
  mounted () {
    // if (this.isLoggingIn) {
    //   this.checkResponse(new URL(window.location.href))
    // } else {
    //   this.generateLoginUrl()
    // }
  },
  methods: {
    ...window.vuex.mapActions([
      'generateLoginUrl',
      'checkResponse'
    ])
  },
  watch: {
    account (val) {
      if (val) {
        const to = window.localStorage.getItem('loginRedirectUrl')
        if (to && to !== 'null' && to !== 'undefined') {
          window.localStorage.removeItem('loginRedirectUrl')
          window.location.href = to
        } else {
          this.$router.push({ name: 'home' })
        }
      }
    },
    loginUrl (val) {
      if (val) {
        window.location.href = val
      }
    }
  }
}
