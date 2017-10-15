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
      processData: false,
      success: function() {
        window.location ='/travelplans/'
      }
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
  $('[id=deleteStep]').each( function() {
    $(this).on( "click", function() {
      let num = $(this).attr('num')
      let index = order.indexOf(num)
      if (index > -1) {
        order.splice(index, 1)
      }
      $('[data-value=' + num  + ']').show()
      $('div[data-id=' + num + ']').remove()
    })
  })
  $('#addStationButton').on('click', function() {
    if(/^\d+$/.test(selectedId)) {
      $('#sortable').append(
          '<div class="completed step" id="travelplan" data-id="' + selectedId +
          '"><i class="sort icon"></i><div class="content" id="category"><div class="title">' +
            selectedStationName + '</div><div class="description">' +
            selectedCategory + '</div><div class="meta">' +
            '<a class="ui mini basic red button" id="deleteStep" num="' +
            selectedId + '">刪除</a></div></div></div>'
        )
      let selector = "div[data-id=" + selectedId + "]"
      let removeButtonSelector = "a[num=" +  selectedId + "]"
      $('.item.active.selected').attr({
        'class': 'item',
        'id': 'hideItem'
      }).hide()
      $('#selectedStationId').empty()
      $(document).on('mouseover', selector, function() {
        $(this).removeClass("completed step")
        $(this).addClass("active step")
      })
      $(document).on('mouseout', selector, function() {
        $(this).removeClass("active step")
        $(this).addClass("completed step")
      })
      $(document).on('click', removeButtonSelector, function() {
        let num = $(this).attr('num')
        let index = order.indexOf(num)
        if (index > -1) {
          order.splice(index, 1)
        }
        $('[data-value=' + num  + ']').show()
        $('div[data-id=' + num + ']').remove()
      })
      order.push(selectedId)
      selectedId = null
    }
  })
  $(".ui.icon.button").click(function () {
    $(this).parent().find("input:file").click();
  })

  $('input:file', '.ui.action.input')
    .on('change', function (e) {
      var name = e.target.files[0].name;
      $('input:text', $(e.target).parent()).val(name);
    })
})
