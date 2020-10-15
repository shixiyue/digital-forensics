function post(params) {
  const form = document.getElementById('adjust-form');

  for (const key in params) {
    if (params.hasOwnProperty(key)) {
      const hiddenField = document.createElement('input');
      hiddenField.type = 'hidden';
      hiddenField.name = key;
      hiddenField.value = params[key];

      form.appendChild(hiddenField);
    }
  }

  document.body.appendChild(form);
  form.submit();
}

window.addEventListener('DOMContentLoaded', function () {
  var image = document.getElementById('modal-image');
  var $modal = $('#modal');
  var selectedCrop = null;
  var dimension = null;
  var cropper = null;

  $modal.on('shown.bs.modal', function () {
    if (cropper !== null) {
      cropper.destroy();
    }
    cropper = new Cropper(image, {
      viewMode: 2,
      rotatable: false,
      scalable: false,
      autoCrop: true,
      data: dimension,
    });
  });

  $('.image-crop').on('click', function () {
    $modal.modal('show');
    selectedCrop = $(this);
    dimension = {
      x: parseInt($(this).find('.x').text()),
      y: parseInt($(this).find('.y').text()),
      width: parseInt($(this).find('.width').text()),
      height: parseInt($(this).find('.height').text()),
    }
  });

  document.getElementById('remove').addEventListener('click', function () {
    $modal.modal('hide');
    if (selectedCrop !== null) {
      post({'remove': true, 'id': selectedCrop.attr('id')});
    }
  });

  document.getElementById('crop').addEventListener('click', function () {
    $modal.modal('hide');
    if (cropper) {
      var dimension = cropper.getData();
      var params = {'adjust': true, 'x': dimension.x, 'y': dimension.y, 
        'width': dimension.width, height: dimension.height,
      };
      if (selectedCrop !== null) {
        params['id'] = selectedCrop.attr('id');
      } else {
        params['id'] = -1;
        params['image_id'] = $('.original-image').attr('id');
      }
      post(params);
    }
  });

  document.getElementById('add').addEventListener('click', function () {
    dimension = null;
    selectedCrop = null;
    $modal.modal('show');
  })

  document.getElementById('next').disabled = true;
  // TODO: Better way
  setTimeout(function(){document.getElementById('next').disabled=false;}, 3000);
});