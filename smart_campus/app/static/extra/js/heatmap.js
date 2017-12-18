var mymap = L.map('mapid').setView([22.998684, 120.218724], 17);
var mymap2 = L.map('mapid2').setView([22.998684, 120.218724], 17);

baseMaps = L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
  attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
  maxZoom: 22,
  id: 'mapbox.streets',
  accessToken: 'pk.eyJ1Ijoiam9ubmUyNjAiLCJhIjoiY2owbmFncmdwMDAwMzJxbnZxMm85eDdtYSJ9.WsKUG0wpHZHUJ0oAWJOqLg'
}).addTo(mymap);

baseMaps2 = L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
  attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
  maxZoom: 22,
  id: 'mapbox.dark',
  accessToken: 'pk.eyJ1Ijoiam9ubmUyNjAiLCJhIjoiY2owbmFncmdwMDAwMzJxbnZxMm85eDdtYSJ9.WsKUG0wpHZHUJ0oAWJOqLg'
}).addTo(mymap2);

var addressPoints = []
var beacon_marker_data;
var markerGroup = L.layerGroup();
$.getJSON('/smart_campus/get_beacon_detect_data/', function (data) {
  //data is the JSON string
  var records = data.data;//_with_each_detection_cnt;
  for (var entry in records) {
    if (entry.count != 0) {
      addressPoints.push([records[entry].lat.toString(), records[entry].lng.toString()])
    }
  }
  //console.log(addressPoints);
  //console.log(data.top3_stations);
  var heat1 = L.heatLayer(addressPoints, { minOpacity: 0.5, radius: 15, blur: 8, gradient: { 0.4: 'blue', 0.6: 'cyan', 0.7: 'lime', 0.8: 'yellow', 1: 'red' } });
  heat1.addTo(mymap);

  beacon_marker_data = data.data_with_each_detection_cnt;
  for (var entry in beacon_marker_data) {
    var marker = L.marker([beacon_marker_data[entry].lat.toString(), beacon_marker_data[entry].lng.toString()]).addTo(markerGroup)
      .bindPopup(beacon_marker_data[entry].beacon_id + "<br>偵測次數：" + beacon_marker_data[entry].count + "<br><a href=/stations/new/ target='_blank'>新增推播點</a>");
  }


});
var latlngs = [[
  [22.9972142750308, 120.220267757466],
  [22.9975056211258, 120.220176562359]], [
  [22.9976883293731, 120.220305308392],
  [22.9976982054875, 120.220235570957]],
  // [22.99842409792, 120.220133647015],
  // [22.9984537260996, 120.218653067639],
  // [22.9984537260996, 120.218502863934],
  // [22.9993845414319, 120.218360706856]
];

//var polyline = L.polyline(latlngs, {color: 'black', smoothFactor: 3, weight:6, opacity: 0.6}).addTo(mymap);
latlngs[1] = latlngs[1].slice(latlngs[1].length - 1);
latlngs[1].push([22.99842409792, 120.220133647015]);
//var polyline2 = L.polyline(latlngs, {color: 'blue', smoothFactor: 3, weight:8, opacity: 0.6}).addTo(mymap);
// // zoom the map to the polyline
//mymap.fitBounds(polyline.getBounds());

var btn_show_marker_clicked = false;
$('#btn_show_marker').on('click', function () {
  if (!beacon_marker_data) return;
  if (!btn_show_marker_clicked) {
    markerGroup.addTo(mymap);
    btn_show_marker_clicked = true;
    $('#btn_show_marker').text('隱藏站點圖釘');
  } else {
    mymap.removeLayer(markerGroup);
    btn_show_marker_clicked = false;
    $('#btn_show_marker').text('顯示站點圖釘');
  }
});
/*
$(document)
    .ready(function() {

      // fix menu when passed
      $('.masthead')
        .visibility({
          once: false,
          onBottomPassed: function() {
		console.log('passed');
            $('.fixed.menu').transition('fade in');
          },
          onBottomPassedReverse: function() {
            $('.fixed.menu').transition('fade out');
          }
        })
      ;

    })
  ;
*/
var dynamicColor = function () {
  var max = 255, min = 0;//Math.floor(Math.random() * (128-20))+20;
  var r = Math.floor(Math.random() * (max - min)) + min;
  var g = Math.floor(Math.random() * (max - min)) + min;
  var b = Math.floor(Math.random() * (max - min)) + min;
  return "rgb(" + r + "," + g + "," + b + ")";
};
var pointGroup = L.layerGroup().addTo(mymap2);
var pathGroup = L.layerGroup().addTo(mymap2);
var current_day_data;
var current_display_hour = 0;
var current_display_minute = 0;
var intervalVar;
var all_user_data;
var latlng_users = [];
var path_colors = [];
var current_day = new Date();
changeDate(0);
function changeDate(val) {
  if (val == 0) {
    current_day = new Date();
  } else {
    var new_date = current_day.getDate() + val;
    current_day.setDate(new_date);
  }
  $('#date').transition('fade').transition('fly right', function () {
    $('#date').text(current_day.getFullYear() + '-' + (current_day.getMonth() + 1) + '-' + current_day.getDate() + '    \n' + 0 + ' 點 ' + 0 + ' 分');
  });
  $('#mapid2').transition('fade').transition('fly left');
  pointGroup.clearLayers();
  pathGroup.clearLayers();
  clearInterval(intervalVar);
  current_display_hour = 0;
  current_display_minute = 0;

  $.ajax({
    type: "POST",
    url: '/smart_campus/get_beacon_detect_data_by_date/',
    data: {
      'year': current_day.getFullYear(),
      'month': current_day.getMonth() + 1,
      'day': current_day.getDate(),
      'csrfmiddlewaretoken': window.CSRF_TOKEN
    },
    success: function (data) {
      //console.log(data.data);
      all_user_data = data.data;
      for (var index in all_user_data) {
        latlng_users[index] = [];
        path_colors[index] = dynamicColor();
      }



      intervalVar = setInterval(function () {

        $('#date').text(current_day.getFullYear() + '-' + (current_day.getMonth() + 1) + '-' + current_day.getDate() + '    \n' + current_display_hour + ' 點 ' + current_display_minute + ' 分');
        for (var index in all_user_data) {
          current_day_data = all_user_data[index];

          for (var entry in current_day_data[current_display_hour][current_display_minute]) {
            data_in_minutes = current_day_data[current_display_hour][current_display_minute];
            var latlng = [data_in_minutes[entry].lat, data_in_minutes[entry].lng];
            latlng_users[index] = latlng_users[index].slice(latlng_users[index].length - 1);
            latlng_users[index].push(latlng);
            //console.log(latlng_users[index]);
            //console.log(latlng);
            L.circleMarker(latlng, {
              radius: 8,
              fillColor: path_colors[index],
              color: "#000",
              weight: 1,
              opacity: 0.5,
              fillOpacity: 0.5
            }).addTo(pointGroup);

            L.polyline(latlng_users[index], { color: path_colors[index], smoothFactor: 10, weight: 2, opacity: 0.6 }).addTo(pathGroup);


          }
        }
        current_display_minute = (current_display_minute + 1) % 60;
        if (current_display_minute == 0) {
          current_display_hour = (current_display_hour + 1) % 24;
          if (current_display_hour == 0) {
            pointGroup.clearLayers();
          }
        }
      }, 250);


    },
    dataType: 'json'
  });
}
