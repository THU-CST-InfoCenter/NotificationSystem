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
    <el-row type="flex" justify="start" style="margin-top: 30px;">
      <el-col :span="2">
        <el-button type="primary" @click="onSubmit()">发送</el-button>
      </el-col>
      <el-col :span="2" align="start" justify="start">
        <el-button type="danger" @click="onClear()">清除</el-button>
      </el-col>
      <el-col :span="3" align="start" justify="start">
        <input type="file" ref="docx" style="display: none" @change="handleDocx">
        <el-button type="success" @click="$refs.docx.click()">从DOCX导入</el-button>
      </el-col>
      <el-col :span="6" align="start" justify="start">
        <el-upload
          ref="upload"
          action
          :file-list="fileList"
          :http-request="myUpload"
          :auto-upload="false"
          :multiple="true"
        >
          <el-button slot="trigger" type="warning">选取文件</el-button>
          <div slot="tip" class="el-upload__tip">请选择附件上传</div>
        </el-upload>
      </el-col>
    </el-row>
  </div>
</template>

<script>
/* eslint-disable */
import E from 'wangeditor';
let mammoth = require('mammoth');

export default {
  methods: {
    myUpload(content) {
      console.log(content)
      let that = this;
    },
    handleDocx(e) {
      let files = e.target.files || e.dataTransfer.files;
      if (!files.length)
        return;
      let name = files[0].name.split(".");
      name = name[name.length - 1];
      const ext = name === "docx" || name === "DOCX";
      if (!ext) {
        swal({ title: "错误", text: "文件必须为DOCX，不支持DOC", icon: "error" });
        return;      
      }
      let reader = new FileReader();
      let that = this;
      reader.readAsArrayBuffer(files[0])
      reader.onload = () => {
        mammoth.convertToHtml({arrayBuffer: reader.result})
        .then(function(res) {
          that.isSelfUpdating = false;
          that.content = res.value;
        }).catch(function(res){
          swal({ title: "错误", text: String(res), icon: "error" });
        }).done();
      };
    },
    onSubmit() {
      if (this.title.trim() === "" || this.content.trim() === "") {
        swal({
          title: "错误",
          text: "通知标题或内容不能为空",
          icon: "error",
          button: "确定"
        });
      } else {
        this.$refs.upload.submit();
      }
    },
    onClear() {
      this.content = "";
    }
  },
  watch: {
    content(val) {
      if(!this.isSelfUpdating)
        this.editor.txt.html(val);
    }
  },
  data() {
    return {
      content: "",
      title: "",
      fileList: [],
      editor: null,
      isSelfUpdating: true,
    };
  },
  mounted() {
    this.editor = new E(this.$refs.editor);
    this.editor.customConfig.onchange = html => { this.content = html; this.isSelfUpdating = true; }
    this.editor.create();
  }
};
</script>