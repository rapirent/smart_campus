$(document).ready(function() {
  $('.search.link.icon').on('click', function() {
    window.location = '/beacons/search?query=' + $('#searchBeacon').val()
  })
})
