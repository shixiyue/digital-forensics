function addImage(url) {
  $('#uploads').append('<div class="col-md-4 col-sm-6 upload-images" style="margin-bottom: 20px;"><img src="' + url + '" class="thumbnail img-fluid"></div>');
};

function redirect(duration, $alert) {
  var timer = duration - 1;
  setInterval(function () {
    if (timer > 0) {
      $alert.text('Upload success, redircting to adjust crops in ' + timer + ' seconds...');
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
    $alert.removeClass('alert-success alert-warning');

    var files = e.target.files;
    var reader;

    if (files && files.length > 0) {
      file = files[0];
      filename = file.name;

      extension = filename.split('.').pop();
      if (extension === "pdf" || extension === "PDF") {
        formData.append('pdf', file);
      }
      else {
        formData.append('image-' + i, file, filename);
        i++;
        reader = new FileReader();
        if (extension === 'tiff' || extension === 'tif') {
          reader.onload = (function (theFile) {
            return function (e) {
              var buffer = e.target.result;
              var tiff = new Tiff({ buffer: buffer });
              var canvas = tiff.toCanvas();
              addImage(canvas.toDataURL());
            };
          })(file);
          reader.readAsArrayBuffer(file);
        } else {
          reader.onload = function (e) {
            addImage(e.target.result);
          };
        }
        reader.readAsDataURL(file);
      }
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
        $alert.show().addClass('alert-success').text('Upload success, redirecting to adjust crops in 8 seconds...');
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