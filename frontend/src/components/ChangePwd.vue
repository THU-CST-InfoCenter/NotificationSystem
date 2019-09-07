<template>
  <el-form
    label-position="left"
    label-width="13vw"
    size="small"
    :model="perinfo"
    status-icon
    :rules="rule"
    ref="form"
  >
    <el-form-item label="原密码" prop="old_pwd">
      <el-input
        v-model="perinfo.old_pwd"
        placeholder="请输入原密码"
        v-bind:style="{ width: elemWidth + 'vw' }"
        :disabled="disabled"
        show-password
      ></el-input>
    </el-form-item>
    <el-form-item label="新密码" prop="new_pwd">
      <el-input
        v-model="perinfo.new_pwd"
        placeholder="请输入新密码"
        v-bind:style="{ width: elemWidth + 'vw' }"
        :disabled="disabled"
        show-password
      ></el-input>
    </el-form-item>
    <el-form-item label="新密码确认" prop="new_pwd_confirm">
      <el-input
        v-model="perinfo.new_pwd_confirm"
        placeholder="请再输入一次新密码"
        v-bind:style="{ width: elemWidth + 'vw' }"
        :disabled="disabled"
        show-password
      ></el-input>
    </el-form-item>
  </el-form>
</template>

<script>
/* eslint-disable */
let md5 = require("js-md5");
import ResChecker from "../api/common";

export default {
  created() {},
  mixins: [ResChecker],
  props: {
    disabled: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    onSubmit() {
      this.$refs.form.validate(v => {
        if (v) {
          let isAdmin = window.sessionStorage.isAdmin == 1;
          var password = {
            old_pwd: md5(this.perinfo.old_pwd),
            new_pwd: md5(this.perinfo.new_pwd)
          };
          this.$http
            .post(
              isAdmin ? "adminChangePassword" : "userChangePassword",
              password
            )
            .then(response => {
              let res = JSON.parse(response.bodyText);
              this.resChecker(res, () =>
                swal({
                  title: "修改成功",
                  icon: "success",
                  button: "确定"
                }).then(val => this.$router.go(0))
              );
            })
            .catch(function(response) {
              console.log(response);
            });
        }
      });
    }
  },
  data() {
    var validatePass2 = (rule, value, callback) => {
      if (value === "") {
        callback(new Error("请再次输入密码"));
      } else if (value !== this.perinfo.new_pwd) {
        callback(new Error("两次输入密码不一致!"));
      } else {
        callback();
      }
    };
    var validatorCommon = (rule, val, cb) => {
      if (val === "") {
        cb(new Error("密码不能为空"));
      } else {
        cb();
      }
    };
    return {
      perinfo: {
        old_pwd: "",
        new_pwd: "",
        new_pwd_confirm: ""
      },
      elemWidth: 25,
      rule: {
        old_pwd: [
          { required: true, validator: validatorCommon, trigger: "blur" }
        ],
        new_pwd: [
          { required: true, validator: validatorCommon, trigger: "blur" }
        ],
        new_pwd_confirm: [
          { required: true, validator: validatePass2, trigger: "blur" }
        ]
      }
    };
  }
};
</script>
