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
  id: 'mapbox.streets',
  accessToken: 'pk.eyJ1Ijoiam9ubmUyNjAiLCJhIjoiY2owbmFncmdwMDAwMzJxbnZxMm85eDdtYSJ9.WsKUG0wpHZHUJ0oAWJOqLg'
}).addTo(mymap2);

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
    console.log(addressPoints);
    console.log(data.top3_stations);
    var heat1 = L.heatLayer(addressPoints,{minOpacity:0.5, radius:15, blur:8, gradient: {0.4: 'blue', 0.6: 'cyan', 0.7: 'lime', 0.8: 'yellow', 1: 'red'}});
    heat1.addTo(mymap);

    beacon_marker_data = data.data_with_each_detection_cnt;
    for (var entry in beacon_marker_data){
        var marker = L.marker([beacon_marker_data[entry].lat.toString(), beacon_marker_data[entry].lng.toString()]).addTo(markerGroup)
            .bindPopup( beacon_marker_data[entry].beacon_id+"<br>偵測次數：" + beacon_marker_data[entry].count +"<br><a href=/stations/new/ target='_blank'>新增推播點</a>");
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
var pointGroup = L.layerGroup().addTo(mymap2);
var current_day_data;
var current_display_hour=0;
var intervalVar;
var current_day = new Date();
changeDate(0);
function changeDate(val) {
  if (val==0){
    current_day = new Date();
  } else {
    var new_date = current_day.getDate()+val;
    current_day.setDate(new_date);
  }
  $('#mapid2').transition('fade').transition('fly left');
  pointGroup.clearLayers();
  clearInterval(intervalVar);
  current_display_hour=0
  $.ajax({
    type: "POST",
    url: '/smart_campus/get_beacon_detect_data_by_date/',
    data: {
      'year': current_day.getFullYear(),
      'month': current_day.getMonth()+1,
      'day': current_day.getDate(),
      'csrfmiddlewaretoken': window.CSRF_TOKEN
    },
    success: function (data) {
      console.log(data[0]);
      current_day_data = data;
      
      intervalVar = setInterval(function (){
        pointGroup.clearLayers();
        $('#date').text(current_day.getFullYear()+'-'+(current_day.getMonth()+1)+'-'+current_day.getDate()+'    \n'+current_display_hour+' 點');
        
        for (var entry in current_day_data[current_display_hour]){
            var marker = L.marker([current_day_data[current_display_hour][entry].lat.toString(), current_day_data[current_display_hour][entry].lng.toString()]).addTo(pointGroup);
        }
        current_display_hour = (current_display_hour+1)%24;
      }, 2000);
      
    },
    dataType: 'json'
  });
}