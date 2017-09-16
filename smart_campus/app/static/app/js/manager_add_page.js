$(document).ready(function() {
  $(".ui.form").form({
    fields: {
      name: {
        identifier: "name",
        rules: [
          {
            type: "empty",
            prompt: "請輸入類別名稱"
          }
        ]
      },
      description: {
        identifier: "description",
        rules: [
          {
            type: "empty",
            prompt: "請輸入描述"
          }
        ]
      },
      iamge: {
        identifier: "iamge",
        rules: [
          {
            type: "empty",
            prompt: "請上傳圖片"
          }
        ]
      }
    }
  });
  $(".ui.selection.dropdown").dropdown();

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
        role: {
          identifier: "role_id",
          rules: [
            {
              type: "empty",
              prompt: "請選擇權限"
            }
          ]
        }
      }
    });
  });
});
