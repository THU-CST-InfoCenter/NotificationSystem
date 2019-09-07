<template>
  <div>
    <el-row type="flex" align="start" justify="start" style="margin-bottom: 10px;">
      <h1>当前选择的数据库</h1>
    </el-row>
    <el-row type="flex" align="start" justify="start">
      <el-col :span="8" align="start" justify="start">
        <el-select v-model="curDatabase" placeholder="未选择" style="width: 100%;">
          <el-option v-for="item in tableData" :key="item.pk" :label="item.alias" :value="item.pk"></el-option>
        </el-select>
      </el-col>
      <el-col :span="6" :offset="1" align="start" justify="start">
        <el-button type="success" @click="handleDBSelection">提交选择</el-button>
      </el-col>
    </el-row>
    <el-divider />
    <el-table :data="tableData">
      <el-table-column prop="alias" label="数据库名称" width="180"></el-table-column>
      <el-table-column prop="system_title" label="系统标题" width="180"></el-table-column>
      <el-table-column prop="set_time" label="设置时间" width="180"></el-table-column>
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
      <el-form label-position="right" label-width="15vw" size="small" :model="dbRule" status-icon>
        <el-form-item label="数据库名称" prop="alias">
          <el-input
            v-model="dbRule.alias"
            placeholder="请输入名称"
            v-bind:style="{ width: elemWidth + 'vw' }"
          ></el-input>
        </el-form-item>
        <el-form-item label="系统标题" prop="system_title">
          <el-input
            v-model="dbRule.system_title"
            placeholder="请输入标题"
            v-bind:style="{ width: elemWidth + 'vw' }"
          ></el-input>
        </el-form-item>
        <el-form-item label="其他设置" prop="other_settings">
          <el-input
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 20 }"
            placeholder="保留用途"
            v-bind:style="{ width: elemWidth + 'vw' }"
            v-model="dbRule.other_settings"
          ></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="handleSubmit">确 定</el-button>
      </span>
    </el-dialog>
    <el-dialog title="提示" :visible.sync="confirmDialogVisible" width="50%">
      <span>删除操作不可恢复，并会清空与之关联的所有用户及通知消息，请确认</span>
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
const db_varname = 'curr_db_id';

export default {
  mixins: [ResChecker],
  data() {
    return {
      elemWidth: 30,
      tableData: [],
      dialogVisible: false,
      confirmDialogVisible: false,
      dialogTitle: "",
      dbRule: {
        alias: "",
        system_title: "",
        other_settings: ""
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
      this.$http.post("getCurrentDBId").then(response => {
        let res = JSON.parse(response.bodyText)
        this.resChecker(res, ()=>{
          that.curDatabase = res.data;
        });
      }).catch(res => console.log(res))
      this.$http
        .post("getDBList")
        .then(response => {
          let json = JSON.parse(response.bodyText);
          this.resChecker(json, () => {
            let arr = JSON.parse(json.data);
            // console.log(arr);
            arr.forEach(element => {
              let data = element.fields;
              data["pk"] = element.pk;
              data["set_time"] = new Date(data["set_time"]).toLocaleString();
              that.tableData.push(data);
            });
          });
        })
        .catch(function(response) {
          console.log(response);
        });
    },
    handleAdd() {
      this.editCallback = null;
      this.dbRule = {
        alias: "",
        system_title: "",
        other_settings: ""
      };
      this.dialogTitle = "添加数据库";
      this.dialogVisible = true;
      let that = this;
      this.addCallback = () => {
        this.$http
          .post("addDB", { data: this.dbRule })
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
    handleDBSelection() {
      this.$http.post("putVariable", {'varname': db_varname, 'value': String(this.curDatabase)}).then(response => {
        console.log(response)
        let res = JSON.parse(response.bodyText)
        this.resChecker(res, ()=>{
          swal({title: "设置成功", icon: "success", button: "确定"});
        })
      }).catch(res => {
        console.log(res);
      });
    },
    handleDelete(idx, row) {
      let that = this;
      this.deleteCallback = () => {
        this.$http
          .post("delDB", { data: this.tableData[idx]["pk"] })
          .then(response => {
            let json = JSON.parse(response.bodyText);
            this.resChecker(json, () => {
              that.dialogVisible = false;
              swal({
                title: "删除成功",
                icon: "success",
                button: "确定"
              }).then(val => {
                if(that.curDatabase === row.pk)
                  that.curDatabase = "";
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
      this.dialogTitle = "编辑数据库 " + row.alias;
      this.dialogVisible = true;
      this.dbRule.alias = this.tableData[idx].alias;
      this.dbRule.system_title = this.tableData[idx].system_title;
      let that = this;
      this.$http
        .post("getDB", { data: this.tableData[idx].pk })
        .then(response => {
          let res = JSON.parse(response.bodyText);
          this.resChecker(res, () => {
            that.dbRule.other_settings = res.data;
            that.editCallback = () => {
              let data = that.dbRule;
              data["pk"] = that.tableData[idx]["pk"];
              that.$http
                .post("editDB", { data: data })
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
          });
        })
        .catch(response => {
          console.log(response);
        });
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