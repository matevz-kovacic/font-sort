import os
import shutil
import argparse
import json
import sys
import requests

from config import DEFAULT_FONT_PATH, DEFAULT_FONT_SUBSETS, DEFAULT_FONT_STYLES


# Utility functions
def fetch_font_list(api_key):
    url = f'https://www.googleapis.com/webfonts/v1/webfonts?key={api_key}'
    print(f'fetching font list from Google Fonts')

    response = requests.get(url)
    response.raise_for_status()
    return response.json()['items']


def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def download_file(url, path):
    response = requests.get(url)
    response.raise_for_status()
    with open(path, 'wb') as f:
        f.write(response.content)


def font_file_name(variant, url):
    file_extension = url.split('.')[-1]
    return f"{variant}.{file_extension}"


# core functions
def print_line(message):
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80

    sys.stdout.write('\r' + message.ljust(terminal_width))
    sys.stdout.flush()

def process_font_files(font, font_dir, styles):
    for variant, url in font['files'].items():

        if variant not in styles:
            continue

        file_name = font_file_name(variant, url)
        file_path = os.path.join(font_dir, file_name)

        print_line(f"Downloading {file_name} for {font['family']}")
        download_file(url, file_path)


def should_process_font(font, font_dir, subsets):
    # process only fonts with requested subset
    font_subsets = font.get('subsets', [])
    is_valid_subset = False
    for subset in subsets:
        if subset in font_subsets:
            is_valid_subset = True
            break

    if not is_valid_subset:
        return False

    json_path = os.path.join(font_dir, 'info.json')
    if not os.path.exists(json_path):
        return True

    existing_font = load_json(json_path)
    if existing_font.get('lastModified') != font.get('lastModified'):
        return True

    return False


def harvest_font(font_info, font_dir, styles):
    if os.path.exists(font_dir):
        shutil.rmtree(font_dir)

    os.makedirs(font_dir)
    process_font_files(font_info, font_dir, styles)

    # To ensure idempotency during the harvesting process, the info file should be saved only after all font files
    # have been successfully processed. This prevents partial state persistence and allows for safe re-execution of
    # the harvesting without data corruption or inconsistency.
    json_path = os.path.join(font_dir, 'info.json')
    save_json(font_info, json_path)


def harvest_fonts(api_key, save_path, subsets, styles):
    fonts = fetch_font_list(api_key)

    for font in fonts:
        font_dir = os.path.join(save_path, font['family'])

        if should_process_font(font, font_dir, subsets):
            try:
                harvest_font(font, font_dir, styles)
            except Exception as e:
                print(f"Error harvesting font {font['family']}: {e}")

    print()


def main():

    parser = argparse.ArgumentParser(description='Fetch and save Google Fonts.')

    parser.add_argument('--api_key', type=str, default=os.getenv('GOOGLE_FONTS_API_KEY'), help='Google Fonts API key.')
    parser.add_argument('--save_path', type=str, default=DEFAULT_FONT_PATH, help='Directory to save the fonts.')
    parser.add_argument('--styles', type=str, nargs='+', default=DEFAULT_FONT_STYLES,
                        help='Harvest only certain font styles (e.g., regular, italic, bold).')
    parser.add_argument('--subset', type=str, nargs='+', default=DEFAULT_FONT_SUBSETS,
                        help='Harvest only subsets of fonts (e.g., latin).')

    args = parser.parse_args()

    if not args.api_key or args.api_key == 'your_google_fonts_api_key':
        parser.error(
            'The --api_key argument is required. Please provide a Google Fonts API key (see https://developers.google.com/fonts/docs/developer_api).')

    harvest_fonts(args.api_key, args.save_path, args.subset, args.styles)


if __name__ == "__main__":
    main()

