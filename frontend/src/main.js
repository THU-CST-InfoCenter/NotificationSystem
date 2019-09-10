/* eslint-disable */
import Vue from 'vue'
import ElementUI from 'element-ui'
import VueResource from 'vue-resource'
import Router from 'vue-router'
import VueObserveVisibility from 'vue-observe-visibility'
import App from './App'
import router from './router'
import swal from 'sweetalert'
import 'element-ui/lib/theme-chalk/index.css'
import CONFIG from './config'


Vue.use(ElementUI)
Vue.use(VueResource)
Vue.use(VueObserveVisibility)
Vue.use(Router)
Vue.config.productionTip = false
Vue.http.options.root = CONFIG.API_URL
Vue.http.options.credentials = true
Vue.http.interceptors.push(function(req, next) {
  req.headers.set('X-Access-Token', window.sessionStorage.token)
  req.headers.set('X-Access-Username', window.sessionStorage.username)
  next()
})

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  components: { App },
  template: '<App/>'
})
