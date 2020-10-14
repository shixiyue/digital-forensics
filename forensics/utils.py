import os

def _get_upload(instance):
    return os.path.join("uploads", str(instance.id))

def _get_crop(instance):
    return os.path.join(_get_upload(instance.original_image), str(instance.id))

def _get_analysis(instance):
    return os.path.join(_get_crop(instance.crop), str(instance.id))

def upload_file_name(instance, filename):
    _, ext = os.path.splitext(filename)
    return os.path.join(_get_upload(instance), "upload" + ext.lower())

def crop_file_name(instance, filename):
    return os.path.join(_get_upload(instance.original_image), os.path.basename(filename))

def analysis_file_name(instance, filename):
    crop_dir, _ = os.path.splitext(instance.crop.image)
    return os.path.join(crop_dir, filename)