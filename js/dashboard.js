function addImage(url) {
  $('#uploads').append('<div class="col-md-4 col-sm-6 upload-images" style="margin-bottom: 20px;"><img src="' + url + '" class="thumbnail img-fluid"></div>');
};

function redirect(duration, $alert) {
  var timer = duration;
  setInterval(function () {
    if (timer > 0) {
      $alert.text('Upload success, redircting to adjust crops in ' + i + ' seconds...');
      timer--;
    } else {
      window.location.replace("http://digitalforensics.report/adjust_crops/");
    }
  }, 1000);
}

window.addEventListener('DOMContentLoaded', function () {
  var image = document.getElementById('image');
  var input = document.getElementById('input');
  var $alert = $('.alert');
  var $modal = $('#modal');
  var cropper = null;
  var file;
  var formData = new FormData();
  var i = 0;
  var filename;

  input.addEventListener('change', function (e) {
    var files = e.target.files;
    var done = function (url) {
      input.value = '';
      image.src = url;
      $alert.hide();
      $modal.modal('show');
    };
    var reader;

    if (files && files.length > 0) {
      file = files[0];
      filename = file.name;
      
      extension = filename.split('.').pop();
      if (extension  === "pdf" || extension === "PDF") {
        formData.append('pdf', file);
      }
      else if (extension === 'tiff' || extension === 'tif') {
        reader = new FileReader();
        reader.onload = (function (theFile) {
          return function (e) {
            var buffer = e.target.result;
            var tiff = new Tiff({ buffer: buffer });
            var canvas = tiff.toCanvas();
            done(canvas.toDataURL());
          };
        })(file);
        reader.readAsArrayBuffer(file);
      } else if (URL) {
        done(URL.createObjectURL(file));
      } else if (FileReader) {
        reader = new FileReader();
        reader.onload = function (e) {
          done(reader.result);
        };
        reader.readAsDataURL(file);
      }
    }
  });

  $modal.on('shown.bs.modal', function () {
    if (cropper !== null) {
      cropper.destroy();
    }
    cropper = new Cropper(image, {
      viewMode: 2,
      rotatable: false,
      scalable: false,
      autoCropArea: 1
    });
  });

  document.getElementById('crop').addEventListener('click', function () {
    $modal.modal('hide');

    if (cropper) {
      var dimension = cropper.getData();

      var canvas = cropper.getCroppedCanvas({
        width: dimension.width,
        height: dimension.height,
      });
      canvas.toBlob(function (blob) {
        formData.append('image-' + i, blob, filename);
        i++;
        canvas = cropper.getCroppedCanvas();
        addImage(canvas.toDataURL());
        cropper.destroy();
        cropper = null;
      });
      $alert.removeClass('alert-success alert-warning');
    }
  });

  document.getElementById('done').addEventListener('click', function () {
    if (cropper !== null) {
      cropper.destroy();
      cropper = null;
    }
    var csrftoken = Cookies.get('csrftoken');
    formData.append('csrfmiddlewaretoken', csrftoken);
    if ($('#is-applying').is(':checked')) {
      formData.append('apply', 'true');
    }
    $.ajax({
      url: 'api/post/',
      type: 'POST',
      data: formData,
      async: false,
      success: function () {
        $alert.show().addClass('alert-success')
        redirect(8, $alert);
      },
      error: function () {
        $alert.show().addClass('alert-danger').text('Upload error');
      },
      complete: function () {
        formData = new FormData();
        $(".upload-images").remove();
      },
      cache: false,
      contentType: false,
      processData: false,
    });
  });
});