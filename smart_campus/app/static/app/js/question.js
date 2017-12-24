$(document).ready(function() {
  $('.ui.inline.floating.dropdown.labeled.search.icon.button').dropdown();
  $(".ui.form").form({
    fields: {
      content: {
        identifier: 'content',
        rules: [
          {
            type: "empty",
            promt: "請輸入題目內容"
          }
        ]
      },
      choice1: {
        identifier: 'choice1',
        rules: [
          {
            type: "empty",
            prompt: "請輸入選項一內容"
          }
        ]
      },
      choice2: {
        identifier: 'choice2',
        rules: [
          {
            type: "empty",
            prompt: "請輸入選項一內容"
          }
        ]
      },
      choice3: {
        identifier: 'choice3',
        rules: [
          {
            type: "empty",
            prompt: "請輸入選項一內容"
          }
        ]
      },
      choice4: {
        identifier: 'choice4',
        rules: [
          {
            type: "empty",
            prompt: "請輸入選項一內容"
          }
        ]
      }
    }
  });
});
