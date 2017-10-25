$(document).ready(function() {
  $(".ui.selection.dropdown").dropdown()

  $(document).ready(function() {
    $(".ui.form").form({
      fields: {
        name: {
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
        },
        password2: {
          identifier: "password2",
          rules: [
            {
              type: "match[password]",
              prompt: "兩次輸入的密碼不一致，請再確認並重新輸入"
            }
          ]
        },
        role: {
          identifier: "role",
          rules: [
            {
              type: "empty",
              prompt: "請選擇權限"
            }
          ]
        }
      }
    })
  })
})
