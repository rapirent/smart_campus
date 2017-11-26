var mymap = L.map('mapid').setView([22.998684, 120.218724], 17);

baseMaps = L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
    attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
    maxZoom: 22,
    id: 'mapbox.streets',
    accessToken: 'pk.eyJ1Ijoiam9ubmUyNjAiLCJhIjoiY2owbmFncmdwMDAwMzJxbnZxMm85eDdtYSJ9.WsKUG0wpHZHUJ0oAWJOqLg'
}).addTo(mymap);

var addressPoints = []

$.getJSON('http://' + $(location).attr('host') + '/smart_campus/get_beacon_detect_data/', function (data) {
    //data is the JSON string
    var records = data.data;
    for (var entry in records){
      addressPoints.push([records[entry].lat.toString(), records[entry].lng.toString()])
    }

    var heat1 = L.heatLayer(addressPoints,{minOpacity:0.6, radius:10, blur:0});
    heat1.addTo(mymap); 
});
