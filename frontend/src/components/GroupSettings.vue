<template>
  <div>
    <el-table :data="tableData">
      <el-table-column prop="groupname" label="组名" width="280"></el-table-column>
      <el-table-column label="操作">
        <template slot-scope="scope">
          <el-button @click="handleEdit(scope.$index, scope.row)" type="text" size="small">编辑</el-button>
          <el-button @click="handleDelete(scope.$index, scope.row)" type="text" size="small">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-row style="margin-top: 30px;" type="flex" justify="start">
      <el-col :span="3">
        <el-button type="primary" @click="handleAdd">新增</el-button>
      </el-col>
    </el-row>
    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="50%">
      <el-form
        label-position="right"
        label-width="15vw"
        size="small"
        :model="groupRule"
        status-icon
      >
        <el-form-item label="组名" prop="groupname">
          <el-input
            v-model="groupRule.groupname"
            placeholder="请输入名称"
            v-bind:style="{ width: elemWidth + 'vw' }"
          ></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="handleSubmit">确 定</el-button>
      </span>
    </el-dialog>
    <el-dialog title="提示" :visible.sync="confirmDialogVisible" width="50%">
      <span>删除组后，该组内所有用户将变为无分组状态，请确认</span>
      <span slot="footer" class="dialog-footer">
        <el-button @click="cancelDelete">取 消</el-button>
        <el-button type="danger" @click="confirmDelete">确 定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
/* eslint-disable */
import ResChecker from "../api/common";

export default {
  mixins: [ResChecker],
  data() {
    return {
      elemWidth: 30,
      tableData: [],
      dialogVisible: false,
      confirmDialogVisible: false,
      dialogTitle: "",
      groupRule: {
        groupname: ""
      },
      deleteCallback: null,
      curDatabase: ""
    };
  },
  created() {
    this.load();
  },
  methods: {
    load() {
      this.tableData = [];
      let that = this;
      this.$http
        .post("getCurrentDBId")
        .then(response => {
          let res = JSON.parse(response.bodyText);
          this.resChecker(res, () => {
            if (res.data === "") {
              swal({
                title: "请先选择数据库",
                icon: "error",
                button: "确定"
              }).then(v => {
                this.$router.push("/admin/db_settings");
                this.$router.go(0);
              });
            } else {
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
                      that.tableData.push(data);
                    });
                  });
                })
                .catch(function(response) {
                  console.log(response);
                });
            }
          });
        })
        .catch(res => console.log(res));
    },
    handleAdd() {
      this.editCallback = null;
      this.groupRule = {
        groupname: ""
      };
      this.dialogTitle = "添加组";
      this.dialogVisible = true;
      let that = this;
      this.addCallback = () => {
        this.$http
          .post("addGroup", { data: this.groupRule })
          .then(response => {
            let json = JSON.parse(response.bodyText);
            this.resChecker(json, () => {
              that.dialogVisible = false;
              swal({
                title: "添加成功",
                icon: "success",
                button: "确定"
              }).then(val => {
                that.load();
              });
            });
          })
          .catch(function(response) {
            console.log(response);
          });
      };
    },
    handleSubmit() {
      if (this.addCallback) {
        this.addCallback();
        this.addCallback = null;
      }
      if (this.editCallback) {
        this.editCallback();
        this.editCallback = null;
      }
    },
    handleDelete(idx, row) {
      let that = this;
      this.deleteCallback = () => {
        this.$http
          .post("delGroup", { data: this.tableData[idx]["pk"] })
          .then(response => {
            let json = JSON.parse(response.bodyText);
            this.resChecker(json, () => {
              that.dialogVisible = false;
              swal({
                title: "删除成功",
                icon: "success",
                button: "确定"
              }).then(val => {
                that.tableData.splice(idx, 1);
              });
            });
          })
          .catch(function(response) {
            console.log(response);
          });
      };
      this.confirmDialogVisible = true;
    },
    handleEdit(idx, row) {
      this.addCallback = null;
      this.dialogTitle = "编辑组 " + row.groupname;
      this.dialogVisible = true;
      this.groupRule.groupname = this.tableData[idx].groupname;
      let that = this;
      this.editCallback = () => {
        let data = that.groupRule;
        data["pk"] = that.tableData[idx]["pk"];
        that.$http
          .post("editGroup", { data: data })
          .then(response => {
            let json = JSON.parse(response.bodyText);
            this.resChecker(json, () => {
              swal({
                title: "修改成功",
                icon: "success",
                button: "确定"
              });
              that.dialogVisible = false;
              that.load();
            });
          })
          .catch(function(response) {
            console.log(response);
          });
      };
    },
    cancelDelete() {
      this.deleteCallback = null;
      this.confirmDialogVisible = false;
    },
    confirmDelete() {
      if (this.deleteCallback) this.deleteCallback();
      this.confirmDialogVisible = false;
    }
  }
};
</script>