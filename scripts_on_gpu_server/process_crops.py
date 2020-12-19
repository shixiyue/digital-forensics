import urllib.request
import os
import json
import requests

from manipulation import ManipulationModel
from algo import ela

DIRECTORY = "temp"
MODEL_LOCATION = "../models/manipulation_model.pth"
get_crops_url = 'http://digitalforensics.report/api/crops/unprocessed/'
post_analysis_url = 'http://digitalforensics.report:8000/api/analysis_crop/'

def setup_session():
    session = requests.session()
    headers = {'Authorization': 'Token 89419aa30d8667c6e47db1c52fdee325341ddc16'}
    session.headers.update(headers)
    return session

def get_list_of_unprocessed_crops(session):
    response = session.get(get_crops_url, timeout=(5, 20))
    if response.ok:
        data = json.loads(response.content)
        return data
    else:
        response.raise_for_status()

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
    files = {"analysis_image": ("manipulation.jpg", open(img_name, 'rb'),'image/jpg')}
    data = {"crop": crop["id"], "analysis_type": analysis_type}
    session.post(post_analysis_url, files=files, data=data)
    # TODO: Add logger

if __name__ == "__main__":
    session = setup_session()
    unprocessed_crops = get_list_of_unprocessed_crops(session)
    manipulation_model = ManipulationModel(MODEL_LOCATION)
    for crop in unprocessed_crops[:1]:
        image_url = crop["image"]
        img_name = download_image(image_url)
        
        manipulation_img = manipulation_model.visualize(img_name)
        post_analysis_img(manipulation_img, "0")
        ela_img = ela(img_name)  
        post_analysis_img(ela_img, "1")  
