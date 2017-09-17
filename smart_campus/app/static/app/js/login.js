$(document).ready(function() {
  $(".ui.form").form({
    fields: {
      email: {
        identifier: "email",
        rules: [
          {
            type: "empty",
            prompt: "請輸入email"
          },
          {
            type: "email",
            prompt: "請輸入正確的email格式"
          }
        ]
      },
      password: {
        identifier: "password",
        rules: [
          {
            type: "empty",
            prompt: "請輸入密碼"
          }
        ]
      }
    }
  })
})
