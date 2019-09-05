<template>
  <div>
    <el-table :data="tableData" style="width: 100%">
      <el-table-column prop="title" label="通知标题" width="400"></el-table-column>
      <el-table-column prop="date" label="时间" width="180"></el-table-column>
      <el-table-column prop="status" label="状态" width="100" v-if="!isAdmin">
        <template slot-scope="scope">
          <el-tag :type="scope.row.status.type">{{scope.row.status.label}}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template slot-scope="scope">
          <el-button size="mini" @click="handleDetails(scope.$index, scope.row)">查看详情</el-button>
          <el-button size="mini" v-if="isAdmin" @click="handleStatus(scope.$index, scope.row)" type="success">查看阅读状态</el-button>
          <el-button
            v-if="isAdmin"
            size="mini"
            type="warning"
            @click="handleDel(scope.$index, scope.row)"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog title="消息内容" :visible.sync="dialogVisible" width="80%">
      <div class="innerHtml">
        <span v-html="msgContent"></span>
      </div>
      <span slot="footer" class="dialog-footer">
        <!--el-button @click="dialogVisible = false">取 消</el-button-->
        <el-button type="primary" @click="dialogVisible = false">确 定</el-button>
      </span>
    </el-dialog>
    <el-dialog title="消息状态" :visible.sync="dialogAdminVisible" width="80%" v-if="isAdmin">
      <div>
        <el-row type="flex" justify="center">
          <el-col :span="24">
            <List :model="msgDetailModel"></List>
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
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="dialogAdminVisible = false">确 定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<style>
.ql-align-center {
  text-align: center;
}
.ql-align-justify {
  text-align: justify;
}
.ql-align-right {
  text-align: right;
}

.innerHtml {
  margin-left: 10%;
  margin-right: 10%;
  text-align: left;
}
</style>

<script>
/* eslint-disable */
import List from "./UneditableList";

export default {
  data() {
    return {
      tableData: [
        {
          title: "test",
          date: "test",
          status: { label: "read", type: "success" },
          link: "test"
        },
        {
          title: "test",
          date: "test",
          status: { label: "reject", type: "danger" },
          link: "test"
        }
      ],
      dialogVisible: false,
      dialogAdminVisible: false,
      msgContent: "",
      isAdmin: window.sessionStorage.isAdmin == 1,
      msgDetailModel: {
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
            type: "tag",
            label: "状态",
            name: "status"
          }
        ],
        tableData: []
      },
      numPages: 0
    };
  },
  created() {
    this.getNotify();
    let fakeData = {
      seq: 0,
      username: 'test',
      name: 'real_name',
      status: {
        type: 'success',
        label: 'read'
      }
    }
    this.msgDetailModel.tableData.push(fakeData)
  },
  components: { List },
  methods: {
    getNotify() {
      console.log("Get notify");
    },
    handleDetails(idx, row) {
      if (
        idx >= 0 &&
        this.tableData != null &&
        this.tableData[idx] != null &&
        this.tableData[idx].link != null
      ) {
        this.msgContent = this.tableData[idx].link;
        this.dialogVisible = true;
      }
    },
    handlePageChange(val) {
      console.log(val)
    },
    handleStatus(idx, row) {
      // fetch and set data
      this.dialogAdminVisible = true;
    },
    handleDel(idx, row) {
      let that = this;
      this.$http
        .post("delNotify", {
          token: window.sessionStorage.token,
          username: window.sessionStorage.username,
          data: { id: row.id, title: row.title }
        })
        .then(response => {
          let res = JSON.parse(response.bodyText);
          if (res.status === 0) {
            that.tableData.splice(idx, 1);
            swal({ title: "删除成功", icon: "success", button: "确定" });
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
        .catch(function(response) {
          console.log(response);
        });
    }
  }
};
</script>