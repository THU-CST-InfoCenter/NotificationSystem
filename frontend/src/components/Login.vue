<template>
  <div>
    <el-row type="flex" justify="center" style="margin: 30px;">
        <img src="../assets/logo.png" />
    </el-row>
    <el-row type="flex" justify="center">
      <el-col :span="10">
        <el-card class="box-card">
          <el-form :model="login" status-icon :rules="rule" ref="login">
            <el-form-item prop="username" label="用户名">
              <el-input prefix-icon="el-icon-user" v-model="login.username" auto-complete="off" />
            </el-form-item>
            <el-form-item prop="password" label="密码" @keyup.enter.native="onSubmit('login')">
              <el-input
                prefix-icon="el-icon-key"
                v-model="login.password"
                type="password"
                auto-complete="off"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-checkbox v-model="isAdmin">管理员登录</el-checkbox>
            </el-form-item>
            <el-form-item>
              <el-button class="btn" type="primary" @click="onSubmit('login')">登录</el-button>
              <el-button class="btn" type="danger" @click="clearFrm()">清除</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
/* eslint-disable */
let md5 = require('js-md5');
import ResChecker from '../api/common'

export default {
  mixins: [ResChecker],
  name: "login",
  data() {
    return {
      isAdmin: false,
      checked: false,
      token: "",
      login: {
        username: "",
        password: ""
      },
      rule: {
        username: [{ required: true, message: "用户名不能为空", trigger: "blur" }],
        password: [{ required: true, message: "密码不能为空", trigger: "blur" }]
      }
    };
  },
  methods: {
    onSubmit: function(login) {
      this.$refs[login].validate(valid => {
        if (valid) {
          this.$http.post(this.isAdmin ? 'adminLogin' : 'userLogin', {'username': this.login.username, 'password': md5(this.login.password)}).then(response => {
            let res = JSON.parse(response.bodyText)
            let that = this
            this.resChecker(res, ()=>{
              window.sessionStorage.token = res.token;
              window.sessionStorage.username = res.username;
              window.sessionStorage.name = res.name;
              window.sessionStorage.isAdmin = that.isAdmin ? 1 : 0;
              that.$router.push(that.isAdmin ? '/admin' : '/home');
            });
          }).catch(function(response) {
            console.log(response)
          })
        }
      });
    },
    clearFrm: function() {
        this.login.username = '';
        this.login.password = '';
    }
  },
  created() {
    if(this.$route.query.message != null) {
      swal({title: this.$route.query.message, text:res.message, button:"确定"});
    }
  }
};
</script>
