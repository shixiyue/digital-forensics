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


class ManipulationModel:
    def __init__(
        self,
        model_weights_location,
        cpu_only=False,
        model_type="COCO-Detection/faster_rcnn_R_101_DC5_3x.yaml",
        threshold=0.65,
    ):
        self.cfg = get_cfg()

        # Load model
        self.cfg.merge_from_file(model_zoo.get_config_file(model_type))
        self.cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1

        # Load custom trained model weights
        self.cfg.MODEL.WEIGHTS = model_weights_location

        # Set threshold
        self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = threshold

        # CPU only turned on
        if cpu_only:
            self.cfg.MODEL.DEVICE = "cpu"

        # Predictor we use to predict
        self.predictor = DefaultPredictor(self.cfg)

        # Set class labels
        MetadataCatalog.get("meta_labels").set(thing_classes=["Manipulation"])
        self.cropping_metadata = MetadataCatalog.get("meta_labels")

        # Load metadata to match label names
        cropping_metadata = MetadataCatalog.get("meta_labels")

    def visualize(self, img_name):
        img = cv2.imread(img_name)
        # Make prediction
        outputs = self.predictor(img)

        v = Visualizer(img[:, :, ::-1], metadata=self.cropping_metadata, scale=1)
        out = v.draw_instance_predictions(outputs["instances"].to("cpu"))

        dirname = os.path.dirname(img_name)
        filename = f"{dirname}/manipulation.jpg"

        cv2.imwrite(filename, out.get_image()[:, :, ::-1])
        print(len(outputs["instances"].to("cpu")))
        return filename

    # Function that gets manipulated parts in image results in format [[x0, y0, x1, y1], ...]
    def medical_bounding_boxes(self, img):
        # Load image or just use image
        if isinstance(img, str):
            img = cv2.imread(img)
        # Make prediction
        outputs = self.predictor(img)
        # Store all medical boxes (class 0)
        all_medical_boxes = []
        classes = outputs["instances"].to("cpu").pred_classes.numpy().astype(int)
        for i in range(len(classes)):
            if classes[i] == 0:
                all_medical_boxes.append(
                    outputs["instances"]
                    ._fields["pred_boxes"]
                    .to("cpu")[i]
                    .__dict__["tensor"][0]
                    .numpy()
                    .astype(int)
                )
        return all_medical_boxes

    # Function that gets medical image boxes results in format [[type, [x0, y0, x1, y1]], ...]
    def all_bounding_boxes(self, img):
        # Load image or just use image
        if isinstance(img, str):
            img = cv2.imread(img)
        # Make prediction
        outputs = self.predictor(img)
        # Store all boxes (class 0 manipulation)
        all_boxes = []
        classes = outputs["instances"].to("cpu").pred_classes.numpy().astype(int)
        for i in range(len(classes)):
            temp = [classes[i]]
            temp.append(
                outputs["instances"]
                ._fields["pred_boxes"]
                .to("cpu")[i]
                .__dict__["tensor"][0]
                .numpy()
                .astype(int)
            )
            all_boxes.append(temp)
        return all_boxes
