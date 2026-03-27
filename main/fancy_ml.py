import os
from typing import List

import cv2
import numpy
from PIL import Image
from PIL import ImageOps


def detect_faces(model: str, image: Image) -> List[List[int]]:
    """Detect faces in an image."""
    assert os.path.exists(model)
    img = ImageOps.grayscale(image)
    # Resize the image so detection is faster.
    img.thumbnail((512,) * 2, Image.LANCZOS)
    # Calculate how much the image was resized so we can restore
    # the bounding box dimensions later.
    scaling_factor = (1.0 * image.size[0]) / img.size[0]
    array = numpy.array(img)

    # `faces` is a list of bounding boxes, with coordinates
    # given as (x_min, y_min, w, h).
    faces = cv2.CascadeClassifier(model).detectMultiScale(array, 1.1, 4)
    # Calculate the bounding boxes in the original-sized image.
    faces = [
        (
            int(x * scaling_factor),
            int(y * scaling_factor),
            int(w * scaling_factor),
            int(h * scaling_factor),
        )
        for x, y, w, h in faces
    ]
    return faces


def protect_faces(faces: List[List[int]], image: Image, ad_filename: str) -> Image:
    """Plaster ads all over the detected faces."""
    ad = Image.open(ad_filename)
    im = image.copy()
    for x, y, w, h in faces:
        thumb = ad.copy()
        thumb.thumbnail((w, h), Image.LANCZOS)
        im.paste(thumb, (x + int((w - thumb.size[0]) / 2), y))

    return im
