<template>
  <div>
    <el-row type="flex" justify="start" align="middle">
      <el-col align="start" :span="2">
        <h1>通知标题</h1>
      </el-col>
      <el-col align="start" justify="start" :span="6">
        <el-input v-model="title" placeholder="请输入通知标题" style="width: 20vw;"></el-input>
      </el-col>
    </el-row>
    <el-divider></el-divider>
    <el-row type="flex" justify="center">
      <el-col :span="24">
        <div ref="editor" style="text-align:left"></div>
      </el-col>
    </el-row>
    <el-divider />
    <el-row type="flex">
      <el-col :span="5" justify="start">
        <h4>通知的用户组(留空为所有用户可见)</h4>
      </el-col>
      <el-col :span="8" justify="start">
        <h4>通知类型</h4>
      </el-col>
    </el-row>
    <el-row type="flex" style="margin-top: 15px;" justify="start" align="middle">
      <el-col :span="5" justify="start">
        <el-select clearable v-model="curGroup" placeholder="请选择" style="width: 100%;">
          <el-option
            v-for="item in groupList"
            :key="item.pk"
            :label="item.groupname"
            :value="item.pk"
          ></el-option>
        </el-select>
      </el-col>
      <el-col :span="8" justify="start">
        <el-switch v-model="needAcRj" active-text="需要用户接受/拒绝" inactive-text="仅需确认已读"></el-switch>
      </el-col>
    </el-row>
    <el-row type="flex" justify="start" style="margin-top: 30px;">
      <el-col :span="2">
        <el-button type="primary" @click="onSend()">发送</el-button>
      </el-col>
      <el-col :span="2" align="start" justify="start">
        <el-button type="danger" @click="onClear()">清除</el-button>
      </el-col>
      <el-col :span="3" align="start" justify="start">
        <input type="file" ref="docx" style="display: none" @change="handleDocx" />
        <el-button type="success" @click="$refs.docx.click()">从DOCX导入</el-button>
      </el-col>
      <el-col :span="6" align="start" justify="start">
        <el-upload
          ref="upload"
          action
          :file-list="fileList"
          :http-request="onSubmit"
          :on-change="handleChange"
          :limit="1"
          :auto-upload="false"
        >
          <el-button slot="trigger" type="warning">选取文件</el-button>
          <div slot="tip" class="el-upload__tip">请选择附件上传，多文件请打包</div>
        </el-upload>
      </el-col>
    </el-row>
  </div>
</template>

<script>
/* eslint-disable */
import E from "wangeditor";
import ResChecker from "../api/common";
let mammoth = require("mammoth");

export default {
  mixins: [ResChecker],
  methods: {
    onSend() {
      if (this.fileList.length == 0) {
        this.onSubmit({});
      } else {
        this.$refs.upload.submit();
      }
    },
    handleChange(file, fileList) {
      this.fileList = [file];
    },
    handleDocx(e) {
      let files = e.target.files || e.dataTransfer.files;
      if (!files.length) return;
      let name = files[0].name.split(".");
      name = name[name.length - 1];
      const ext = name === "docx" || name === "DOCX";
      if (!ext) {
        swal({
          title: "错误",
          text: "文件必须为DOCX，不支持DOC",
          icon: "error"
        });
        return;
      }
      let reader = new FileReader();
      let that = this;
      reader.readAsArrayBuffer(files[0]);
      reader.onload = () => {
        mammoth
          .convertToHtml({ arrayBuffer: reader.result })
          .then(function(res) {
            that.isSelfUpdating = false;
            that.content = res.value;
          })
          .catch(function(res) {
            swal({ title: "错误", text: String(res), icon: "error" });
          })
          .done();
      };
    },
    onSubmit(content) {
      if (this.title.trim() === "" || this.content.trim() === "") {
        swal({
          title: "错误",
          text: "通知标题或内容不能为空",
          icon: "error",
          button: "确定"
        });
      } else {
        let form = new FormData();
        if (this.fileList.length > 0) form.append("file", content.file);
        form.append("title", this.title);
        form.append("content", this.content);
        form.append("visible_group_id", this.curGroup);
        form.append("notification_type", this.needAcRj ? 1 : 0);
        this.$http
          .post("sendNotification", form, {
            headers: { "Content-Type": "multipart/form-data" },
            progress(e) {
              if (e.lengthComputable) {
                let percent = (e.loaded / e.total) * 100;
                if (content.onProgress)
                  content.onProgress({ percent: percent });
              }
            }
          })
          .then(response => {
            let res = JSON.parse(response.bodyText);
            this.resChecker(res, () => {
              this.$refs.upload.clearFiles();
              if (content.onSuccess) content.onSuccess();
              swal({
                title: "通知发送成功",
                icon: "success",
                button: "确定"
              }).then(v => this.$router.go(0));
            });
          });
      }
    },
    onClear() {
      this.content = "";
    }
  },
  watch: {
    content(val) {
      if (!this.isSelfUpdating) this.editor.txt.html(val);
    }
  },
  data() {
    return {
      content: "",
      title: "",
      fileList: [],
      editor: null,
      isSelfUpdating: true,
      groupList: [],
      curGroup: "",
      needAcRj: false,
    };
  },
  mounted() {
    this.editor = new E(this.$refs.editor);
    this.editor.customConfig.onchange = html => {
      this.content = html;
      this.isSelfUpdating = true;
    };
    this.editor.create();
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
  }
};
</script>