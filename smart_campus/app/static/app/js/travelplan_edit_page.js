$(document).ready(function() {
  let selectedId, selectedStationName, selectedCategory
  $('.ui.inline.floating.dropdown.labeled.search.icon.button').dropdown({
    onChange: function(value, text, $selectedItem) {
                selectedId = value
                selectedStationName = text
                selectedCategory = $selectedItem.attr('category')
              }
  })

  let el = document.getElementById('sortable')
  let order = {}
  Sortable.create(el, {
    store: {
      /**
        * Get the order of elements. Called once during initialization.
        * @param   {Sortable}  sortable
        * @returns {Array}
        */
      get: function (sortable) {
        return order = sortable.toArray()
      },
      /**
        * Save the order of elements. Called onEnd (when the item is dropped).
        * @param {Sortable}  sortable
        */
      set: function (sortable) {
        order = sortable.toArray()
      }
    }
  })

  $('#submitButton').on('click', function() {
    let postData = new FormData()
    postData.append('name', $('#name').val())
    postData.append('description', $('textarea').val())
    if($('input[type=file]')[0].files[0]) {
      postData.append('image', $('input[type=file]')[0].files[0])
    }
    postData.append('order', JSON.stringify(order))
    postData.append('csrfmiddlewaretoken', window.CSRF_TOKEN)
    $.ajax({
      url: window.location.pathname,
      type: 'POST',
      data: postData,
      cache: false,
      contentType: false,
      processData: false
    })
  })

  $('[id=travelplan]').each( function() {
    $(this).on( "mouseover", function() {
      $(this).removeClass("completed step")
      $(this).addClass("active step")
    })
  })
  $('[id=travelplan]').each( function() {
    $(this).on( "mouseout", function() {
      $(this).removeClass("active step")
      $(this).addClass("completed step")
    })
  })
  $('#addStationButton').on('click', function() {
    if(/^[\d\.]$/.test(selectedId)) {
      $('#sortable').append(
          '<div class="completed step" id="travelplan" data-id="' + selectedId +
          '"><div class="content" id="category"><div class="title">' +
            selectedStationName + '</div><div class="description">' +
            selectedCategory + '</div></div></div>'
        )
      let selector = "div[data-id=" + selectedId + "]"
      $('.item.active.selected').remove()
      $('#selectedStationId').empty()
      $(document).on('mouseover', selector, function() {
        $(this).removeClass("completed step")
        $(this).addClass("active step")
      })
      $(document).on('mouseout', selector, function() {
        $(this).removeClass("active step")
        $(this).addClass("completed step")
      })
      order.push(selectedId)
    }
  })
  $(".ui.icon.button").click(function () {
    $(this).parent().find("input:file").click();
  });

  $('input:file', '.ui.action.input')
    .on('change', function (e) {
      var name = e.target.files[0].name;
      $('input:text', $(e.target).parent()).val(name);
    });
})