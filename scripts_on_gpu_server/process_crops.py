import urllib.request
import os
import json
import requests
import shutil

from manipulation import ManipulationModel
from algo import ela
from logmodule import LogModule

logger = LogModule()

DIRECTORY = "temp"
MODEL_LOCATION = "/home/ubuntu/digital-forensics/models/manipulation_model.pth"
get_crops_url = "http://digitalforensics.report/api/crops/unprocessed/"
post_analysis_url = "http://digitalforensics.report:8000/api/analysis_crop/"


def setup_session():
    session = requests.session()
    headers = {"Authorization": "Token 89419aa30d8667c6e47db1c52fdee325341ddc16"}
    session.headers.update(headers)
    return session


def get_list_of_unprocessed_crops(session):
    try:
        response = session.get(get_crops_url, timeout=(5, 20))
        if response.ok:
            data = json.loads(response.content)
            return data
        else:
            logger.error("Failed to retrieve list of unprocessed crops: " + response.status_code)
    except Exception as e:
        logger.error("Exception: " + str(e))


def download_image(url):
    if url is None:
        return
    filename = os.path.basename(url)
    dirname, _ = os.path.splitext(filename)
    dirname = os.path.join(DIRECTORY, dirname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    filename = os.path.join(dirname, filename)
    urllib.request.urlretrieve(url, filename)
    return filename


def post_analysis_img(img_name, analysis_type):
    files = {"analysis_image": ("manipulation.jpg", open(img_name, "rb"), "image/jpg")}
    data = {"crop": crop["id"], "analysis_type": analysis_type}
    response = session.post(post_analysis_url, files=files, data=data)
    if response.ok:
        logger.info("Upload analysis image, " + str(data))
    else:
        logger.error("Failed to upload analysis image, " + response.status_code)


if __name__ == "__main__":
    session = setup_session()
    unprocessed_crops = get_list_of_unprocessed_crops(session)
    manipulation_model = ManipulationModel(MODEL_LOCATION)
    for crop in unprocessed_crops:
        image_url = crop["image"]
        img_name = download_image(image_url)
        if not img_name:
            continue

        manipulation_img = manipulation_model.visualize(img_name)
        if manipulation_img:
            post_analysis_img(manipulation_img, "0")
        ela_img = ela(img_name)
        post_analysis_img(ela_img, "1")
    shutil.rmtree(DIRECTORY)    
