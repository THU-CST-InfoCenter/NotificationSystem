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
          <el-button
            size="mini"
            v-if="isAdmin"
            @click="handleStatus(scope.$index, scope.row)"
            type="success"
          >查看阅读状态</el-button>
          <el-button
            v-if="isAdmin"
            size="mini"
            type="warning"
            @click="handleDel(scope.$index, scope.row)"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog
      title="消息内容"
      :visible.sync="dialogVisible"
      width="80%"
      :close-on-click-modal="isAdmin"
      :show-close="isAdmin"
    >
      <el-row>
        <div class="innerHtml">
          <span v-html="msgContent"></span>
        </div>
      </el-row>
      <el-divider v-if="msgAttachment.length > 0" />
      <el-row
        v-for="(item,idx) in msgAttachment"
        v-bind:key="idx"
        style="margin-top: 3px; margin-left: 10%;"
        justify="start"
        type="flex"
      >
        <el-link type="primary" @click="downloadAttachment(item)">附件下载: {{item}}</el-link>
      </el-row>
      <span slot="footer" class="dialog-footer">
        <el-button v-if="isAdmin" type="primary" @click="dialogVisible = false">确 定</el-button>
        <div v-if="!isAdmin">
          <el-button @click="dialogVisible = false">取 消</el-button>
          <el-button type="primary" @click="changeStatus(1)">确认已读</el-button>
          <el-button type="success" @click="changeStatus(2)">接受</el-button>
          <el-button type="danger" @click="changeStatus(3)">拒绝</el-button>
        </div>
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
import ResChecker from "../api/common";

const MSG_STATUS_ARR = [
  {
    label: "未读",
    type: ""
  },
  {
    label: "已读",
    type: "info"
  },
  {
    label: "已接受",
    type: "success"
  },
  {
    label: "已拒绝",
    type: "danger"
  }
];

export default {
  mixins: [ResChecker],
  data() {
    return {
      tableData: [],
      dialogVisible: false,
      dialogAdminVisible: false,
      msgContent: "",
      msgId: 0,
      msgAttachment: [],
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
      username: "test",
      name: "real_name",
      status: {
        type: "success",
        label: "read"
      }
    };
    this.msgDetailModel.tableData.push(fakeData);
  },
  components: { List },
  methods: {
    changeStatus(status) {
      this.$http
        .post("changeNotificationStatus", { id: this.msgId, status: status })
        .then(res => {
          this.resChecker(res.body, () => {
            this.dialogVisible = false;
            this.tableData.forEach(e => {
              if (e.id === this.msgId) {
                e.status = MSG_STATUS_ARR[status];
              }
            });
          });
        });
    },
    downloadAttachment(fname) {
      this.$http
        .post(
          this.isAdmin ? "downloadAttachmentAdmin" : "downloadAttachmentUser",
          { id: this.msgId, filename: fname },
          { responseType: "blob" }
        )
        .then(response => {
          if (response.body.status !== undefined) {
            if (response.body.status !== 0) {
              swal({
                title: "出错了",
                text: response.body.message,
                icon: "error",
                button: "确定"
              }).then(val => {
                if (response.body.status === -1) {
                  that.$router.push("/");
                }
              });
              return;
            }
          }
          const link = document.createElement("a");
          let blob = new Blob([response.data], {
            type: "application/octet-stream"
          });
          link.style.display = "none";
          link.href = URL.createObjectURL(blob);
          link.setAttribute("download", fname);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        })
        .catch(res => console.log(res));
    },
    getNotify() {
      this.$http
        .post(this.isAdmin ? "getNotifications" : "getPersonalNotifications")
        .then(response => {
          let res = JSON.parse(response.bodyText);
          this.resChecker(res, () => {
            res.data.forEach(e => {
              e.date = new Date(e.date).toLocaleString();
            });
            this.tableData = res.data;
          });
        })
        .catch(res => console.log(res));
    },
    handleDetails(idx, row) {
      if (
        idx >= 0 &&
        this.tableData != null &&
        this.tableData[idx] != null &&
        this.tableData[idx].link != null
      ) {
        this.dialogVisible = true;
        this.msgContent = "";
        this.msgAttachment = [];
        this.msgId = 0;
        this.$http
          .post(
            this.isAdmin
              ? "getNotificationDetailAdmin"
              : "getNotificationDetail",
            { id: row.id }
          )
          .then(response => {
            this.resChecker(response.body, () => {
              this.msgContent = response.body.data.content;
              if (response.body.data.attachment_arr.length > 0)
                this.msgAttachment = response.body.data.attachment_arr;
              this.msgId = row.id;
            });
          })
          .catch(res => console.log(res));
      }
    },
    handlePageChange(val) {
      this.$http
        .post("getNotificationStatus", { id: this.msgId, page: val })
        .then(res => {
          this.resChecker(res.body, () => {
            this.numPages = res.body.data.page_cnt;
            this.msgDetailModel.tableData = res.body.data.curr_entries;
          });
        })
        .catch(res => console.log(res));
    },
    handleStatus(idx, row) {
      // fetch and set data
      this.msgDetailModel.tableData = [];
      this.msgId = row.id;
      this.handlePageChange(1);
      this.dialogAdminVisible = true;
    },
    handleDel(idx, row) {
      let that = this;
      this.$http
        .post("delNotification", {
          data: { id: row.id, title: row.title }
        })
        .then(response => {
          let res = JSON.parse(response.bodyText);
          this.resChecker(res, () => {
            that.tableData.splice(idx, 1);
            swal({ title: "删除成功", icon: "success", button: "确定" });
          });
        })
        .catch(function(response) {
          console.log(response);
        });
    }
  }
};
</script>