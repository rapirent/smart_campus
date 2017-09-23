$(document).ready(function() {
  $('.circular.search.link.icon').on('click', function() {
    window.location = '/stations/search?query=' + $('#searchStation').val()
  })
})
