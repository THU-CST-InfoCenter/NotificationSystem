/* eslint-disable */
const resChecker = function(res, onSuccess, onFail=null) {
    if(res.status === 0) {
        onSuccess(res);
    } else {
        if(onFail == null) {
            swal({
                title: "出错了",
                text: res.message,
                icon: "error",
                button: "确定"
              }).then(val => {
                if (res.status === -1) {
                  this.$router.push("/");
                }
              });
        } else onFail(res);
    }
}

export default resChecker;