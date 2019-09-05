/* eslint-disable */
import Router from 'vue-router'
import Login from '@/components/Login'
import UserMain from '@/components/UserMain'
import AdminMain from '@/components/AdminMain'
import Notify from '@/components/Notify'
import SendNotify from '@/components/SendNotify'
import UserSettings from '@/components/UserSettings'
import DBSettings from '@/components/DBSettings'
import GroupSettings from '@/components/GroupSettings'

const beforeEachHook = (to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title
  }
  if (to.meta.needLogin && window.sessionStorage.token == null) {
    next({
      path: '/',
      query: { message: '未登录，现在跳转到登录页面' }
    })
  } else if (to.meta.needAdmin && window.sessionStorage.isAdmin == 0) {
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
      /**
       * Router for common users
       */
      path: '/home',
      component: UserMain,
      meta: userMeta,
      children: [
        {
          path: 'notify',
          component: Notify,
          meta: userMeta
        },
      ]
    },
    {
      /**
       * Router for admins
       */
      path: '/admin',
      component: AdminMain,
      meta: adminMeta,
      children: [
        {
          path: 'view_notify',
          component: Notify,
          meta: adminMeta
        },
        {
          path: 'send_notify',
          component: SendNotify,
          meta: adminMeta
        },{
          path: 'user_settings',
          component: UserSettings,
          meta: adminMeta
        },{
          path: 'db_settings',
          component: DBSettings,
          meta: adminMeta
        },{
          path: 'group_settings',
          component: GroupSettings,
          meta: adminMeta
        }
      ]
    },
    {
      path: '*',
      redirect: '/'
    }
  ]
})

router.beforeEach(beforeEachHook)

export default router
