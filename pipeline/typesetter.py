from PIL import Image, ImageDraw, ImageFont
import numpy as np

class Typesetter:
    def __init__(self, font_path=None):
        self.font_path = font_path # Path to a .ttf file

    def draw_text_on_image(self, inpainted_image_path, detected_items, output_path):
        """
        Draw translated text onto the inpainted image.
        """
        # Load the inpainted image using Pillow
        img = Image.open(inpainted_image_path).convert("RGB")
        draw = ImageDraw.Draw(img)

        for item in detected_items:
            box = item['box']
            translated_text = item.get('translated_text', '')
            if not translated_text:
                continue

            # Calculate bounding box dimensions
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            
            box_width = x_max - x_min
            box_height = y_max - y_min

            if box_width <= 0 or box_height <= 0:
                continue

            # Start with a heuristic text size
            font_size = int(box_height * 0.45) if box_height else 20
            font_size = max(10, min(font_size, 80))
            
            lines = []
            font = None

            # Loop to find an optimal font size where the wrapped text fits inside the box
            while font_size >= 8:
                try:
                    if self.font_path:
                        font = ImageFont.truetype(self.font_path, font_size)
                    else:
                        font = ImageFont.load_default()
                except Exception:
                    font = ImageFont.load_default()

                words = translated_text.split()
                lines = []
                current_line = []
                
                for word in words:
                    test_line = " ".join(current_line + [word])
                    # Measure pixel width of text
                    try:
                        line_width = font.getlength(test_line)
                    except AttributeError:
                        try:
                            line_width = font.getsize(test_line)[0]
                        except:
                            line_width = len(test_line) * (font_size * 0.6) # fallback approximation
                            
                    if line_width <= box_width * 0.95:
                        current_line.append(word)
                    else:
                        if not current_line: # Even one word is too big
                            lines.append(word)
                            current_line = []
                        else:
                            lines.append(" ".join(current_line))
                            current_line = [word]
                            
                if current_line:
                    lines.append(" ".join(current_line))
                    
                line_height = font_size * 1.2
                total_height = len(lines) * line_height
                
                # Break if it fits, or if we can't shrink anymore
                if total_height <= box_height * 0.95 or font_size == 8:
                    break
                    
                font_size -= 2

            text_x = x_min + (box_width / 2)
            text_y = y_min + (box_height / 2)
            
            line_height = font_size * 1.2
            y_offset = text_y - (len(lines) * line_height / 2) + (font_size * 0.5)
            
            # Use thick outline so it's readable over any background
            stroke_width = max(1, int(font_size * 0.08))
            
            for line in lines:
                draw.text(
                    (text_x, y_offset), 
                    line, 
                    font=font, 
                    fill="#111111", 
                    anchor="mm",
                    stroke_width=stroke_width,
                    stroke_fill="white"
                )
                y_offset += line_height

        img.save(output_path)
        return output_path
