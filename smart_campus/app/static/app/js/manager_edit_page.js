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
