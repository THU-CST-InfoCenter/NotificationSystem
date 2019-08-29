/* eslint-disable */
import Router from 'vue-router'
import Login from '@/components/Login'

const beforeEachHook = (to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title
  }
  if (to.meta.needLogin && window.sessionStorage.token == null) {
    next({
      path: '/',
      query: { message: '未登录，现在跳转到登录页面' }
    })
  } else if (to.meta.needAdmin && window.sessionStorage.user_type !== '2') {
    next({
      path: '/home'
    })
  } else next()
}

const userTitle = '通知系统'
const adminTitle = '通知系统-管理后台'
const userMeta = {
  needLogin: true,
  title: userTitle
}
const adminMeta = {
  needLogin: true,
  needAdmin: true,
  title: adminTitle
}

const router = new Router({
  mode: 'history',
  routes: [
    {
      path: '/',
      component: Login,
      meta: {
        title: '系统登陆'
      }
    },
    {
      path: '*',
      redirect: '/'
    }
  ]
})

router.beforeEach(beforeEachHook)

export default router
