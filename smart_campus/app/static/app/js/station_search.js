$(document).ready(function() {
  $('.search.link.icon').on('click', function() {
    window.location = '/stations/search?query=' + $('#searchStation').val()
  })
})
