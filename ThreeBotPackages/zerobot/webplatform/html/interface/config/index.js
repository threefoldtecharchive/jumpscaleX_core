import config from './config.local.js'

export default ({
  ...config,
  salutations: ['Mr', 'Miss', 'Mme'],
  description: ['Work', 'Home', 'Mobile'],
  appId: `${window.location.host}`,
  redirect_url: '/login',
  scope: ''
})
