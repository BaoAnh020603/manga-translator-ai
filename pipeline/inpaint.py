import cv2
import numpy as np

class Inpainter:
    def __init__(self):
        pass

    def inpaint_image(self, image_path, detected_items, output_path=None):
        """
        Inpaint (remove) text from the original image based on bounding boxes,
        using Smart Threshold Masking to preserve the background art.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Could not load image at {image_path}")

        # Create a blank mask with the same dimensions as the image (1 channel)
        mask = np.zeros(img.shape[:2], dtype=np.uint8)

        # Convert image to grayscale for thresholding
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        for item in detected_items:
            box = item['box']
            # Convert float coordinates to integers
            pts = np.array(box, np.int32)
            
            # Find the bounding rectangle of the polygon to crop
            x, y, w, h = cv2.boundingRect(pts)
            
            # Ensure boundaries are within image
            x = max(0, x)
            y = max(0, y)
            w = min(w, img.shape[1] - x)
            h = min(h, img.shape[0] - y)
            
            if w <= 0 or h <= 0:
                continue
                
            # Crop the grayscale region containing the text
            roi_gray = gray[y:y+h, x:x+w]
            
            # Apply Otsu's thresholding to isolate text pixels (assuming dark text on light bg or vice versa)
            # We use an adaptive threshold to handle varying comic shades
            thresh = cv2.adaptiveThreshold(
                roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Create a polygon mask for just this exact text box 
            # to make sure we don't accidentally grab artifacts outside the box but inside the rect
            poly_mask = np.zeros((h, w), dtype=np.uint8)
            shifted_pts = pts - [x, y]
            cv2.fillPoly(poly_mask, [shifted_pts], 255)
            
            # Bitwise AND: Only keep thresh pixels that are INSIDE the polygon
            clean_text_mask = cv2.bitwise_and(thresh, poly_mask)
            
            # Add the cleaned text mask back to the global mask
            mask[y:y+h, x:x+w] = cv2.bitwise_or(mask[y:y+h, x:x+w], clean_text_mask)

        # Dilate the finely detailed mask slightly to cover edge antialiasing of the text
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_dilated = cv2.dilate(mask, kernel, iterations=1)

        # Apply inpainting using the Telea algorithm on just the text pixels!
        inpainted_img = cv2.inpaint(img, mask_dilated, inpaintRadius=5, flags=cv2.INPAINT_TELEA)

        if output_path:
            cv2.imwrite(output_path, inpainted_img)

        return inpainted_img
