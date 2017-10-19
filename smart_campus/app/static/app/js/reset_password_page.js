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
      }
    }
  })
})
