$(".ui.icon.button").click(function () {
  $(this).parent().find("input:file").click();
});

$('input:file', '.ui.action.input')
  .on('change', function (e) {
    var name = e.target.files[0].name;
    $('input:text', $(e.target).parent()).val(name);
  });
$('.ui.radio.checkbox')
  .checkbox();
$(document).ready(function() {
  $(".ui.form").form({
    fields: {
      name: {
        identifier: "name",
        rules: [
          {
            type: "empty",
            prompt: "請輸入行程名稱"
          }
        ]
      }
    }
  })
})
