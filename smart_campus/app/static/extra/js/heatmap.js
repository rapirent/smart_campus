var mymap = L.map('mapid').setView([22.998684, 120.218724], 17);

baseMaps = L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
    attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
    maxZoom: 22,
    id: 'mapbox.streets',
    accessToken: 'pk.eyJ1Ijoiam9ubmUyNjAiLCJhIjoiY2owbmFncmdwMDAwMzJxbnZxMm85eDdtYSJ9.WsKUG0wpHZHUJ0oAWJOqLg'
}).addTo(mymap);

var addressPoints = []
var beacon_marker_data;
var markerGroup = L.layerGroup();
$.getJSON('http://' + $(location).attr('host') + '/smart_campus/get_beacon_detect_data/', function (data) {
    //data is the JSON string
    var records = data.data;//_with_each_detection_cnt;
    for (var entry in records){
      if (entry.count != 0) {
        addressPoints.push([records[entry].lat.toString(), records[entry].lng.toString()])
      }
    }
    console.log(addressPoints)
    var heat1 = L.heatLayer(addressPoints,{minOpacity:0.5, radius:15, blur:8, gradient: {0.4: 'blue', 0.6: 'cyan', 0.7: 'lime', 0.8: 'yellow', 1: 'red'}});
    heat1.addTo(mymap);

    beacon_marker_data = data.data_with_each_detection_cnt;
    for (var entry in beacon_marker_data){
        var marker = L.marker([beacon_marker_data[entry].lat.toString(), beacon_marker_data[entry].lng.toString()]).addTo(markerGroup)
            .bindPopup("偵測次數：" + beacon_marker_data[entry].count);
    }
});

var btn_show_marker_clicked = false;
$('#btn_show_marker').on('click', function() {
    if (!beacon_marker_data) return;
    if(!btn_show_marker_clicked){
        markerGroup.addTo(mymap);
        btn_show_marker_clicked = true;
        $('#btn_show_marker').text('隱藏站點圖釘');
    }else{
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
$('#section-1').scroll(function () {$('#mapid').transition('pulse')}); 
