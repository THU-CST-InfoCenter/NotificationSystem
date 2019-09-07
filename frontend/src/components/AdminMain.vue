<template>
  <div>
    <el-container class="main" direction="vertical">
      <el-header class="main-header" style="align-items: center;">
        <el-row align="middle" type="flex">
          <el-col :xs="5" :sm="4" :md="3" :lg="2" :xl="1">
            <el-link :underline="false" type="info" style="font-size: 18px;">管理后台</el-link>
          </el-col>
          <el-col :xs="8" :sm="16" :md="18">
            <el-menu
              default-active="0"
              style="padding: 0;"
              mode="horizontal"
              background-color="#545c64"
              text-color="#fff"
              active-text-color="#ffd04b"
            >
              <el-menu-item index="0">管理员主页</el-menu-item>
            </el-menu>
          </el-col>
          <el-col
            v-bind:style="{ 'font-size': textFontSize + 'px'}"
            :xs="5"
            :sm="4"
            :md="3"
            :lg="2"
          >你好, {{ name }}</el-col>
          <el-col :xs="3" :sm="3" :md="2">
            <el-link
              v-bind:style="{ 'font-size': textFontSize + 'px'}"
              :underline="false"
              type="primary"
              @click="changePassword"
            >修改密码</el-link>
          </el-col>
          <el-col :xs="1" :sm="2" :md="1">
            <el-link
              v-bind:style="{ 'font-size': textFontSize + 'px'}"
              :underline="false"
              type="primary"
              @click="exitLogin"
            >退出</el-link>
          </el-col>
        </el-row>
      </el-header>
      <el-container style="overflow: hidden;">
        <el-aside style="width: auto" class="hidden-xs-only">
          <div>
            <el-menu
              :class="'menu'"
              :default-active="defaultActive"
              class="el-menu-vertical-demo"
              @select="handleSelect"
              background-color="#545c64"
              text-color="#fff"
              active-text-color="#ffd04b"
            >
              <el-menu-item
                v-for="(item, index) in sidebarItems"
                v-bind:key="index"
                :index="String(index)"
              >
                <i v-bind:class="item.icon"></i>
                <span slot="title">{{ item.name }}</span>
              </el-menu-item>
            </el-menu>
          </div>
        </el-aside>
        <el-main>
          <router-view></router-view>
        </el-main>
      </el-container>
      <el-footer class="main-footer" height="50px">
        <div v-html="footerMsg">{{ footerMsg }}</div>
      </el-footer>
    </el-container>
    <el-dialog
      title="密码修改"
      :visible.sync="dialogFormVisible"
      width="50%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
      :center="true"
    >
      <el-row type="flex" justify="center">
        <el-col :span="24" :push="2">
          <ChangePwd ref="perinfo"></ChangePwd>
        </el-col>
      </el-row>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible = false">取 消</el-button>
        <el-button type="primary" @click="changePasswordSubmit();">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>
<style>
* {
  padding: 0;
  margin: 0;
}
</style>
<style scoped lang="scss">
$header-height: 60px;
$background-color: #545c64;
$color: #fff;

.main {
  height: 100vh;
  min-width: 800px;
  min-height: 600px;
  overflow: hidden;

  aside {
    overflow: visible;
    height: 100%;
    background-color: $background-color;
    color: $color;
    .menu {
      width: 100%;
      border-right: 0;
    }
  }

  .main-header {
    background-color: $background-color;
    color: $color;
  }

  .main-footer {
    text-align: center;
    background-color: $background-color;
    color: $color;
    line-height: 50px;
  }

  .text-info {
    font-size: 20px;
  }
}
</style>

<script>
/* eslint-disable */
import "element-ui/lib/theme-chalk/display.css";
import { footer } from "../api/basicSettings";
import ChangePwd from "./ChangePwd"

export default {
  data() {
    return {
      defaultActive: "0",
      textFontSize: 14,
      sidebarCol: 2.5,
      name: "",
      sidebarItems: [],
      footerMsg: footer,
      dialogFormVisible: false
    };
  },
  created() {
    this.sidebarItems = [
        {
          link: "/admin/view_notify",
          name: "查看通知",
          icon: "el-icon-message"
        },
        {
          link: "/admin/send_notify",
          name: "发送通知",
          icon: "el-icon-upload2"
        },
        {
          link: "/admin/user_settings",
          name: "用户管理",
          icon: "el-icon-user"
        },
        {
          link: "/admin/group_settings",
          name: "用户组设置",
          icon: "el-icon-connection"
        },
        {
          link: "/admin/db_settings",
          name: "数据库选择",
          icon: "el-icon-setting"
        },
    ];
    let foundItem = false;
    for (let idx in this.sidebarItems) {
      if (this.sidebarItems[idx].link === this.$route.path) {
        this.defaultActive = String(idx);
        foundItem = true;
        break;
      }
    }
    if (!foundItem) {
      this.$router.push(this.sidebarItems[0].link);
    }
    if (
      window.sessionStorage.token != null &&
      window.sessionStorage.name != null
    )
      this.name = window.sessionStorage.name;
  },
  methods: {
    handleSelect(key, keyPath) {
      let val = parseInt(key);
      if (
        this.sidebarItems != null &&
        val >= 0 &&
        val < this.sidebarItems.length &&
        this.sidebarItems[val]
      ) {
        this.$router.push(this.sidebarItems[val].link);
      }
    },
    exitLogin() {
      window.sessionStorage.clear();
      this.$router.push("/");
    },
    changePassword() {
      this.dialogFormVisible = true;
    },
    changePasswordSubmit() {
      this.$refs.perinfo.onSubmit();
    }
  },
  components: { ChangePwd }
};
</script>

