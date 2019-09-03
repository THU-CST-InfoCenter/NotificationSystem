<template>
  <div>
    <el-row type="flex" justify="start" align="start">
      <el-col :span="4">
        <el-button type="success" :click="addUserFromExcel">从Excel导入用户</el-button>
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
    }
  }
};
</script>

