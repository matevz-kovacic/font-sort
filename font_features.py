import os
import sys
import argparse
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import torch
from torchvision import transforms
import timm

from config import DEFAULT_FEATURES_CHARACTERS, DEFAULT_FEATURES_TEXTS


def print_line(message):
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80

    sys.stdout.write('\r' + message.ljust(terminal_width))
    sys.stdout.flush()


# Load pre-trained Vision Transformer model
model = timm.create_model('vit_base_patch16_224', pretrained=True)
model.eval()

# Transformation for input image without resizing
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])


#
# font features
#
def extract_features(img):
    img = transform(img).unsqueeze(0)
    with torch.no_grad():
        features = model.forward_features(img).flatten().numpy()
    return features


def generate_text_image(font_path, text, image_size=(224, 224), padding=10):
    # Initialize font size and create a draw object
    font_size = 10
    font_image = Image.new('RGB', image_size, 'white')
    draw = ImageDraw.Draw(font_image)

    # Increase font size until the text fits the image
    while True:
        font_pillow = ImageFont.truetype(font_path, font_size)

        bbox = draw.textbbox((0, 0), text, font=font_pillow)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        if (text_width + padding) > image_size[0] or (text_height + padding) > image_size[1]:
            font_size -= 1
            break
        font_size += 1

    # Load the font with the final size
    font_pillow = ImageFont.truetype(font_path, font_size)

    # Create the final blank image
    font_image = Image.new('RGB', image_size, 'white')
    draw = ImageDraw.Draw(font_image)

    bbox = draw.textbbox((0, 0), text, font=font_pillow)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (image_size[0] - text_width) / 2 - bbox[0]
    y = (image_size[1] - text_height) / 2 - bbox[1]

    # Draw the text on the image
    draw.text((x, y), text, fill='black', font=font_pillow)

    return font_image, text_width, text_height


def calculate_glyph_density(font_image, text_width, text_height):
    # Convert the image to grayscale and calculate the glyph density
    grayscale_image = font_image.convert('L')
    image_array = np.array(grayscale_image)
    threshold = 240
    non_background_pixels = np.sum(image_array < threshold)

    # Calculate the bounding box area
    bbox_area = text_width * text_height

    # Glyph density is the ratio of non-background pixels to bounding box area
    glyph_density = non_background_pixels / bbox_area if bbox_area > 0 else 0

    return glyph_density


def font_features(font_file_name, alphabet, texts):
    features = []
    glyph_densities = []

    # Process each character in the alphabet
    for char in alphabet:
        char_img, char_width, char_height = generate_text_image(font_file_name, char)

        char_features = extract_features(char_img)
        features.append(char_features)

        glyph_density = calculate_glyph_density(char_img, char_width, char_height)
        glyph_densities.append(glyph_density)

    # Process each string in the text array
    for txt in texts:
        text_img, text_width, text_height = generate_text_image(font_file_name, txt)
        text_features = extract_features(text_img)
        features.append(text_features)

    # Concatenate all character features into a single feature vector
    features = np.concatenate(features)

    # Calculate the average thickness ratio
    average_glyph_density = np.mean(glyph_densities)

    return features, average_glyph_density


#
# computing font features for font directory
#
def create_font_features_files(font_file, alphabet, texts, features_file_name, density_file_name):
    features, glyph_density = font_features(font_file, alphabet, texts)
    np.save(features_file_name, features)

    Path(density_file_name).write_text(f'{glyph_density}\n')


def compute_font_features(font_dir, font_name, alphabet, texts, force_recompute):
    font_file_path = os.path.join(font_dir, font_name)
    features_file_name = os.path.join(font_dir, f'{font_name}.features')
    density_file_name = os.path.join(font_dir, f'{font_name}.density')

    if force_recompute or not os.path.exists(features_file_name) or not os.path.exists(density_file_name):
        print_line(f'Computing font features for: {font_dir}')
        create_font_features_files(font_file_path, alphabet, texts, features_file_name, density_file_name)


def enumerate_fonts(fonts_dir, alphabet, texts, force_recompute):
    """Enumerate all .ttf font names and compute their features."""
    for font_name in os.listdir(fonts_dir):
        font_dir = os.path.join(fonts_dir, font_name)
        if os.path.isdir(font_dir):
            for font_file in os.listdir(font_dir):
                if font_file.endswith('.ttf'):
                    try:
                        compute_font_features(font_dir, font_file, alphabet, texts, force_recompute)
                    except Exception as e:
                        print(f"\nAn error occurred while processing font {font_dir}/{font_file} : {e}")

    print()


def main():
    parser = argparse.ArgumentParser(description='Compute an save font features')

    parser.add_argument('--font_path', type=str, default='./fonts', help='Directory with fonts.')
    parser.add_argument('--characters', type=str, default=DEFAULT_FEATURES_CHARACTERS,
                        help='Characters for font comparisons in each font.')
    parser.add_argument('--texts', type=str, nargs='+', default=DEFAULT_FEATURES_TEXTS,
                        help='Array of texts for font comparisons.')
    parser.add_argument('--force_features_recompute', type=bool, default=True,
                        help='Force features recompute. Must be true unless font features characters, , font subsets, and font styles remain unchanged from the previous run')
    args = parser.parse_args()

    enumerate_fonts(args.font_path, args.characters, args.texts, args.force_features_recompute)


if __name__ == "__main__":
    main()
