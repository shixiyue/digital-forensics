window.addEventListener('DOMContentLoaded', function () {
    var image = document.getElementById('image');
    var input = document.getElementById('input');
    var $alert = $('.alert');
    var $modal = $('#modal');
    var cropper;
    var file;

    input.addEventListener('change', function (e) {
      var files = e.target.files;
      var done = function (url) {
        input.value = '';
        image.src = url;
        $alert.hide();
        $modal.modal('show');
      };
      var reader;
      var url;

      if (files && files.length > 0) {
        file = files[0];

        if (URL) {
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
      cropper = new Cropper(image, {
        viewMode: 3,
        rotatable: false,
        scalable: false
      });
    }).on('hidden.bs.modal', function () {
      cropper.destroy();
      cropper = null;
    });

    document.getElementById('crop').addEventListener('click', function () {
      $modal.modal('hide');

      if (cropper) {
        var dimension = cropper.getData();
        $alert.removeClass('alert-success alert-warning');
        var formData = new FormData();
        formData.append('image', file);
        formData.append('x', dimension.x); 
        formData.append('y', dimension.y); 
        formData.append('width', dimension.width);
        formData.append('height', dimension.height);
        var csrftoken = Cookies.get('csrftoken');
        formData.append('csrfmiddlewaretoken', csrftoken);
        $.ajax({
          url: 'api/post/',
         type: 'POST',
         data: formData,
         async: false,
         success: function () {
          $alert.show().addClass('alert-success').text('Upload success');
        },

        error: function () {
          $alert.show().addClass('alert-warning').text('Upload error');
        },
         complete: function () {
          $alert.show().addClass('alert-success').text('Upload success');
         },
         cache: false,
         contentType: false,
         processData: false
     });   
        /*
        canvas.toBlob(function (blob) {
          var formData = new FormData();

          formData.append('avatar', blob, 'avatar.jpg');
          $.ajax('https://jsonplaceholder.typicode.com/posts', {
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,

            xhr: function () {
              var xhr = new XMLHttpRequest();

              xhr.upload.onprogress = function (e) {
                
              };

              return xhr;
            },


          });
        });*/
      }
    });
  });