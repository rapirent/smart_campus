var map;

function initMap() {
  // Create a map object and specify the DOM element for display.
  map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 22.998684, lng: 120.218724},
    zoom: 16
  });
  // Add marker of beacons
  for(var i=0; i < location_arr.length; i++){
    addMarker(
      location_arr[i][0],
      location_arr[i][1],
      location_arr[i][2]
    )
  }
}

function addMarker(title, lat, lng) {
  var marker = new google.maps.Marker({
    position: {lat, lng},
    map: map,
    title: title
  });

  marker.addListener('click', function() {
    map.setCenter(marker.getPosition())
    $("#selectbasic").val(marker.getTitle())
    $("#lat_input").val(marker.getPosition().lat())
    $("#lng_input").val(marker.getPosition().lng())
  })
}

let imgCount=1;
// Add new file upload field and radio button
$("#addimage").click( function(){

  if (imgCount < MAX_IMGS){
    imgCount++;

    $('#uiAddImage').append(
      '<div class="ui action input" id="select' + imgCount + '">' +
      '<input type="text" placeholder="img ' +
      imgCount +   '" readonly="">' +
      '<input id="img' + imgCount +
      '" name="img' + imgCount +
      '" type="file" accept="image/*" style="display: none;">' +
      '<div class="ui icon button" id="select' + imgCount +
      'Button"><i class="attach icon"></i></div>' +
      '</div>'
    )
    $("#select" + imgCount + 'Button').click(function () {
      $(this).parent().find("input:file").click();
    });

    $('input:file', '#select' + imgCount)
      .on('change', function (e) {
        var name = e.target.files[0].name;
        $('input:text', $(e.target).parent()).val(name);
      });
    $('.grouped.fields').append(
      '<div class="field"><div class="ui radio checkbox"><input type="radio" name="main_img_num" id="radios-' +
      imgCount + '" value="' + imgCount + '" tabindex="0" class="hidden"><label>' +
      '圖片' +  imgCount + '</label></div></div>')
    $('.ui.radio.checkbox').checkbox()

  }
})

$(document).ready(function() {
  $(".ui.form").form({
    fields: {
      name: {
        identifier: "name",
        rules: [
          {
            type: "empty",
            prompt: "請輸入站點名稱"
          }
        ]
      },
      category: {
        identifier: "category",
        rules: [
          {
            type: "empty",
            prompt: "請輸入類別"
          }
        ]
      },
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
      beacon: {
        identifier: "beacon",
        rules: [
          {
            type: "empty",
            prompt: "請於地圖點選Beacon"
          }
        ]
      },
    }
  })
})
