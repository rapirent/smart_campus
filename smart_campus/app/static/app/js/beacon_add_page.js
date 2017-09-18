$(document).ready(function() {
  $(".ui.selection.dropdown").dropdown();

  $(document).ready(function() {
    $(".ui.form").form({
      fields: {
        lng: {
          identifier: "lng",
          rules: [
            {
              type: "empty",
              prompt: "請輸入經度"
            }
          ]
        },
        lat: {
          identifier: "lat",
          rules: [
            {
              type: "empty",
              prompt: "請輸入緯度"
            }
          ]
        },
        beacon_id: {
          identifier: "beacon_id",
          rules: [
            {
              type: "empty",
              prompt: "請選擇beacon id"
            }
          ]
        },
        name: {
          identifier: "name",
          rules: [
            {
              type: "empty",
              prompt: "請輸入名稱"
            }
          ]
        }
      }
    });
  });
});
