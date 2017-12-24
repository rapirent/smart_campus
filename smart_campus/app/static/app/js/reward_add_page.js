$(document).ready(function () {
  $(".ui.icon.button").click(function () {
    $(this).parent().find("input:file").click()
  })

  $('input:file', '.ui.action.input')
    .on('change', function (e) {
      var name = e.target.files[0].name
      $('input:text', $(e.target).parent()).val(name)
    })
  $('.ui.radio.checkbox').checkbox()
  $(".ui.form").form({
    fields: {
      name: {
        identifier: "name",
        rules: [{
          type: "empty",
          prompt: "請輸入類別名稱"
        }]
      },
      description: {
        identifier: "description",
        rules: [{
          type: "empty",
          prompt: "請輸入描述"
        }]
      },
      iamge: {
        identifier: "iamge",
        rules: [{
          type: "empty",
          prompt: "請上傳圖片"
        }]
      }
    }
  })
})
