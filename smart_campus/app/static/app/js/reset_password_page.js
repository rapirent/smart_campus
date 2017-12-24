$(document).ready(function() {
  $(".ui.form").form({
    fields: {
      password: {
        identifier: "password",
        rules: [
          {
            type: "empty",
            prompt: "請輸入密碼"
          }
        ]
      },
      password2: {
        identifier: "password2",
        rules: [
          {
            type: "match[password]",
            prompt: "兩次輸入的密碼不一致，請再確認並重新輸入"
          }
        ]
      }
    }
  })
})
