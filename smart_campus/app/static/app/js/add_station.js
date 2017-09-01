var map;
function initMap() {
  // Create a map object and specify the DOM element for display.
  map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 22.997496, lng: 120.216508},
    zoom: 14
  });
  //Add marker of beacons
  for(var i=0; i < location_arr.length ;i++){
    addMarker(location_arr[i][0], location_arr[i][1], location_arr[i][2]);
  }
}

function addMarker(title, lat, lng) {
  var marker = new google.maps.Marker({
    position: {lat, lng},
    map: map,
    title: title
  });

  marker.addListener('click', function() {
    map.setZoom(16);
    map.setCenter(marker.getPosition());
    $("#selectbasic").val(marker.getTitle());
    $("#lat_input").val(marker.getPosition().lat());
    $("#lng_input").val(marker.getPosition().lng())
  });
}

var imgcnt=1;

$("#btn_addimage").click(function(){
  imgcnt++;
  if(imgcnt<=4)
  {
    var imgupload_div = document.getElementById("img_upload");
    var newcontent = document.createElement('div');

    newcontent.innerHTML = "<div class='col-md-4'>Photo "+imgcnt+":<input id=img"+imgcnt+" name=img"+imgcnt+" class='form-control-file' type=file accept=image/*></div>";

    while (newcontent.firstChild) {
        imgupload_div.appendChild(newcontent.firstChild);
    }

    var img_sel_div = document.getElementById("radios-img-select");
    var newcontent = document.createElement('div');
    newcontent.innerHTML = "<label class=radio-inline for=radios-"+imgcnt+"><input type=radio name=radios id=radios-"+imgcnt+" value="+imgcnt+"> "+imgcnt+" </label>";
    while (newcontent.firstChild) {
        img_sel_div.appendChild(newcontent.firstChild);
    }
  }   
});
