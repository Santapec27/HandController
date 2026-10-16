from PIL import Image, ImageDraw

def create_icon():
    # Create an image with transparent background
    image = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a simple hand-like icon (a circle representing a palm, and lines for fingers)
    # Palm
    draw.ellipse((16, 24, 48, 56), fill=(73, 109, 137), outline=(255, 255, 255), width=2)
    # Fingers
    draw.line((24, 24, 20, 8), fill=(73, 109, 137), width=6)
    draw.line((32, 24, 32, 4), fill=(73, 109, 137), width=6)
    draw.line((40, 24, 44, 10), fill=(73, 109, 137), width=6)
    draw.line((48, 36, 56, 24), fill=(73, 109, 137), width=6) # thumb
    
    image.save('assets/icon.ico', format='ICO')
    print("Icon generated successfully.")

if __name__ == '__main__':
    create_icon()
