<template>
  <div>
    <el-row type="flex" justify="start" align="start">
      <el-col :span="8" justify="start" align="start">
        <el-upload
          ref="upload"
          action
          :multiple="false"
          accept=".xlsx,.xls"
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
  </div>
</template>

<script>
/* eslint-disable */
import List from "./UneditableList";

const numElemPerPage = 15;

export default {
  data() {
    return {
      numPages: 0,
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
      fileList: [],
      linkCb: function(link) {
        console.log(link)
      },
    };
  },
  components: { List },
  created() {
    this.fakeAddDataHelper();
  },
  methods: {
    handlePageChange(val) {
      console.log(val)
    },
    fakeAddDataHelper() {
      let template = {
        seq: 0,
        username: "zx1239856",
        name: "my_name",
        link: {
          link: "zx1239856",
          label: "编辑用户"
        }
      };
      for(let i = 0; i < 10; ++i)
        this.model.tableData.push(template)
    },
    addUserFromExcel() {
      console.log('add_user')
    },
    handleChange(file, fileList) {
      let name = file.name.split(".");
      name = name[name.length - 1];
      const ext = name === "xls" || name === "XLS" || name === "xlsx" || name === "XLSX";
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
      form.append("name_col", 1);
      form.append("pwd_col", 3);
      form.append("username_col", 0);
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
          if (res.status === 0) {
            content.onSuccess();
            that.$refs.upload.clearFiles();
            swal({
              title: "文件上传成功",
              icon: "success",
              button: "确定"
            });
          } else {
            let that = this;
            swal({
              title: "出错了",
              text: res.message,
              icon: "error",
              button: "确定"
            }).then(val => {
              if (res.status === -1) {
                that.$router.push("/");
              }
            });
          }
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

