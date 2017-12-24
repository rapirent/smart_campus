$(document).ready(function () {
  $('.ui.menu .ui.dropdown').dropdown({
    on: 'hover'
  })
  $('.ui.sidebar').sidebar('attach events', '.launch.button', 'slide out');
})
