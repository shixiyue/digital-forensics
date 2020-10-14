# import some common libraries
import numpy as np
import os, cv2
import matplotlib.pyplot as plt

# import some common detectron2 utilities
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.data import MetadataCatalog
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.utils.visualizer import ColorMode

from django.core.files.base import File

class CroppingModel():
    def __init__(self, model_weights_location, cpu_only = True, model_type = "COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml", threshold = 0.65):
        self.cfg = get_cfg()
        
        # Load model
        self.cfg.merge_from_file(model_zoo.get_config_file(model_type))
        self.cfg.MODEL.ROI_HEADS.NUM_CLASSES = 3
        
        # Load custom trained model weights
        self.cfg.MODEL.WEIGHTS = model_weights_location
        
        # Set threshold
        self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = threshold
        
        # CPU only turned on
        if cpu_only:
            self.cfg.MODEL.DEVICE = 'cpu'
        
        # Predictor we use to predict
        self.predictor = DefaultPredictor(self.cfg)
        
        # Set class labels
        MetadataCatalog.get("meta_labels").set(thing_classes=["Medical", "Graph", "Icon"])
        self.cropping_metadata = MetadataCatalog.get("meta_labels")
        
        # Load metadata to match label names
        cropping_metadata = MetadataCatalog.get("meta_labels")
    
    def visualize(self, img, save_image_path = None):
        # Load image or just use image
        if isinstance(img, str):
            img = cv2.imread(img)
        # Make prediction
        outputs = self.predictor(img)
        
        v = Visualizer(img[:, :, ::-1], metadata = self.cropping_metadata, scale = 1)
        out = v.draw_instance_predictions(outputs["instances"].to("cpu"))
        
        print(len(outputs['instances'].to("cpu")), "bounding boxes")
        
        plt.figure(figsize=(20,20))
        
        _ = plt.imshow(cv2.cvtColor(out.get_image()[:, :, ::-1], cv2.COLOR_BGR2RGB))
        
        if save_image_path is not None:
            cv2.imwrite(save_image_path, out.get_image()[:, :, ::-1])
    
    # Function that gets medical image boxes results in format [[x0, y0, x1, y1], ...]
    def medical_bounding_boxes(self, img_id, img):
        from .models import Image, Crop

        # Load image or just use image
        print(img)
        if isinstance(img, str):
            img = cv2.imread(img)
        # Make prediction
        outputs = self.predictor(img)
        # Store all medical boxes (class 0)
        medical_boxes = []
        classes = outputs['instances'].to("cpu").pred_classes.numpy().astype(int)
        for i in range(len(classes)):
            if classes[i] == 0:
                medical_boxes.append(outputs['instances']._fields['pred_boxes'].to("cpu")[i].__dict__['tensor'][0].numpy().astype(int))
        for x0, y0, x1, y1 in medical_boxes:
            crop_img = img[y0:y1, x0:x1]
            crop = Crop.objects.create(original_image=Image.objects.get(id=img_id), 
                                           image=File(crop_img))
            print(crop.id)
            
    
    # Function that gets medical image boxes results in format [[type, [x0, y0, x1, y1]], ...]
    def all_bounding_boxes(self, img):
        # Load image or just use image
        if isinstance(img, str):
            img = cv2.imread(img)
        # Make prediction
        outputs = self.predictor(img)
        # Store all boxes (class 0 medical, 1 graph, 2 icons)
        all_boxes = []
        classes = outputs['instances'].to("cpu").pred_classes.numpy().astype(int)
        for i in range(len(classes)):
            temp = [classes[i]]
            temp.append(outputs['instances']._fields['pred_boxes'].to("cpu")[i].__dict__['tensor'][0].numpy().astype(int))
            all_boxes.append(temp)
        return all_boxes

