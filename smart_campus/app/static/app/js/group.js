$(document).ready(function() {
  $(".ui.form").form({
    fields: {
      name: {
        identifier: "name",
        rules: [
          {
            type: "empty",
            prompt: "請輸入群組名稱"
          }
        ]
      }
    }
  })
})
