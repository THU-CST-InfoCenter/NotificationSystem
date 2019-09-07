<template>
  <div>
    <el-row type="flex">
      <el-col :span="24">
        <el-form :inline="true" :model="conf_model">
          <el-form-item label="用户名所在列">
            <el-input-number v-model="conf_model.username_col" :min="1" label="用户名所在列"></el-input-number>
          </el-form-item>
          <el-form-item label="姓名所在列">
            <el-input-number v-model="conf_model.name_col" :min="1" label="姓名所在列"></el-input-number>
          </el-form-item>
          <el-form-item label="初始密码所在列">
            <el-input-number v-model="conf_model.pwd_col" :min="1" label="初始密码所在列"></el-input-number>
          </el-form-item>
          <el-form-item label="起始行号">
            <el-input-number v-model="conf_model.start_row" :min="1" label="起始行号"></el-input-number>
          </el-form-item>
          <el-form-item label="终止行号">
            <el-input-number v-model="conf_model.end_row" :min="1" label="终止行号"></el-input-number>
          </el-form-item>
        </el-form>
      </el-col>
    </el-row>
    <el-row type="flex" justify="center" align="center">
      <el-col :span="8" justify="center" align="center">
        <el-upload
          ref="upload"
          action
          :multiple="false"
          accept=".xlsx, .xls"
          :on-change="handleChange"
          :file-list="fileList"
          :limit="1"
          :http-request="myUpload"
          :auto-upload="false"
        >
          <el-button slot="trigger" type="primary">从Excel导入用户</el-button>
          <el-button style="margin-left: 20px;" type="success" @click="onSubmitDocument">上传</el-button>
          <div slot="tip" class="el-upload__tip">只能上传Excel文件, 大小不能超过10M</div>
        </el-upload>
      </el-col>
    </el-row>
    <el-divider></el-divider>
    <el-row type="flex" justify="center">
      <el-col :span="24">
        <List :model="model" :linkCb="linkCb"></List>
      </el-col>
    </el-row>
    <el-row type="flex" justify="center" style="margin-top: 1vh">
      <el-col :span="24">
        <el-pagination
          :hide-on-single-page="true"
          background
          layout="prev, pager, next"
          :page-count="numPages"
          @current-change="handlePageChange"
        ></el-pagination>
      </el-col>
    </el-row>
    <el-dialog
      title="用户信息修改"
      :visible.sync="dialogFormVisible"
      width="50%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
      :center="true"
    >
      <el-row type="flex" justify="center">
        <el-col :span="24" :push="2">
          <el-form
            label-position="left"
            label-width="13vw"
            size="small"
            :model="perinfo"
            status-icon
            ref="form"
          >
            <el-form-item label="密码重置" prop="pwd">
              <el-input
                v-model="perinfo.pwd"
                placeholder="请输入新密码，留空为不变"
                v-bind:style="{ width: elemWidth + 'vw' }"
                show-password
              ></el-input>
            </el-form-item>
            <el-form-item label="邮箱设置" prop="email">
              <el-input
                v-model="perinfo.email"
                placeholder="请输入邮箱"
                v-bind:style="{ width: elemWidth + 'vw' }"
              ></el-input>
            </el-form-item>
            <el-form-item label="用户组选择" prop="group">
              <el-select
                clearable
                v-model="perinfo.group"
                placeholder="请选择用户组"
                v-bind:style="{ width: elemWidth + 'vw' }"
              >
                <el-option
                  v-for="item in groupList"
                  :key="item.pk"
                  :label="item.groupname"
                  :value="item.pk"
                ></el-option>
              </el-select>
            </el-form-item>
          </el-form>
        </el-col>
      </el-row>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible = false; resetPerInfo();">取 消</el-button>
        <el-button type="primary" @click="changeUserFormSubmit();">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
/* eslint-disable */
import List from "./UneditableList";
import ResChecker from "../api/common";
let md5 = require('js-md5');

const numElemPerPage = 15;
let this_ptr = null;

export default {
  mixins: [ResChecker],
  data() {
    return {
      elemWidth: 25,
      perinfo: {
        pwd: "",
        email: "",
        group: "",
        id: ""
      },
      groupList: [],
      numPages: 0,
      conf_model: {
        username_col: 1,
        pwd_col: 1,
        name_col: 1,
        start_row: 1,
        end_row: 1
      },
      model: {
        tableColumn: [
          {
            type: "seq",
            label: "#",
            name: "seq",
            colWidth: "50%"
          },
          {
            type: "text",
            label: "用户名",
            name: "username"
          },
          {
            type: "text",
            label: "姓名",
            name: "name"
          },
          {
            type: "link",
            label: "操作",
            name: "link"
          }
        ],
        tableData: []
      },
      dialogFormVisible: false,
      fileList: [],
      linkCb: function(link) {
        this_ptr.perinfo = {
          pwd: "",
          email: "",
          group: "",
          id: ""
        };
        this.$http
          .post("getUserInfo", { id: link })
          .then(res => {
            this_ptr.resChecker(res.body, data => {
              this_ptr.dialogFormVisible = true;
              this_ptr.perinfo.email = data.data.email;
              this_ptr.perinfo.group = data.data.group;
              this_ptr.perinfo.id = data.data.id;
            });
          })
          .catch(res => console.log(res));
      }
    };
  },
  components: { List },
  created() {
    this_ptr = this;
    this.handlePageChange(1);
    this.$http
      .post("getGroupList")
      .then(response => {
        let json = JSON.parse(response.bodyText);
        this.resChecker(json, () => {
          let arr = JSON.parse(json.data);
          // console.log(arr);
          arr.forEach(element => {
            let data = element.fields;
            data["pk"] = element.pk;
            this.groupList.push(data);
          });
        });
      })
      .catch(function(response) {
        console.log(response);
      });
  },
  methods: {
    changeUserFormSubmit() {
      if(this.perinfo.pwd.trim() != "")
        this.perinfo.pwd = md5(this.perinfo.pwd);
      this.$http.post("changeUserInfoAdmin", this.perinfo).then(res=> {
        res = res.body;
        this.resChecker(res, ()=>{
          swal({
              title: "信息修改成功",
              icon: "success",
              button: "确定"
          }).then(v => {
            this.dialogFormVisible = false;
            this.resetPerInfo();
          });
        })
      });
    },
    resetPerInfo() {
      this.perinfo = {
          pwd: "",
          email: "",
          group: "",
          id: ""
      };
    },
    handlePageChange(val) {
      this.$http.post("getUserList", { page: val }).then(res => {
        this.resChecker(res.body, () => {
          res = res.body;
          this.model.tableData = res.data.curr_entries;
          this.numPages = res.data.page_cnt;
        });
      });
    },
    handleChange(file, fileList) {
      let name = file.name.split(".");
      name = name[name.length - 1];
      const ext =
        name === "xls" || name === "XLS" || name === "xlsx" || name === "XLSX";
      const size = file.size < 10 * 1024 * 1024;
      if (!ext) {
        swal({ title: "错误", text: "文件必须为EXCEL", icon: "error" });
        this.$refs.upload.uploadFiles = [];
      } else if (!size) {
        swal({ title: "错误", text: "文件大小不能超过10M", icon: "error" });
        this.$refs.upload.uploadFiles = [];
      } else {
        this.$refs.upload.uploadFiles = [file];
      }
    },
    myUpload(content) {
      let that = this;
      let form = new FormData();
      form.append("file", content.file);
      form.append("token", window.sessionStorage.token);
      form.append("username", window.sessionStorage.username);
      form.append("name_col", this.conf_model.name_col - 1);
      form.append("pwd_col", this.conf_model.pwd_col - 1);
      form.append("username_col", this.conf_model.username_col - 1);
      form.append("start_row", this.conf_model.start_row - 1);
      form.append("end_row", this.conf_model.end_row - 1);
      this.$http
        .post("createStudentAccounts", form, {
          headers: { "Content-Type": "multipart/form-data" },
          progress(e) {
            if (e.lengthComputable) {
              let percent = (e.loaded / e.total) * 100;
              content.onProgress({ percent: percent });
            }
          }
        })
        .then(response => {
          let res = JSON.parse(response.bodyText);
          this.resChecker(res, () => {
            content.onSuccess();
            that.$refs.upload.clearFiles();
            swal({
              title: "操作成功",
              text: "增加/修改了 " + res.newusers + " 个用户",
              icon: "success",
              button: "确定"
            }).then(v => that.$router.go(0));
          });
        })
        .catch(function(res) {
          console.log(res);
        });
    },
    onSubmitDocument() {
      this.$refs.upload.submit();
    }
  }
};
</script>

