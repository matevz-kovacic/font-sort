# Font Sorting System

This project is a system for sorting fonts according to visual similarity [see blog post](https://ideatum.ai/blog/better-font-list). It consists of three main scripts:
- `font_harvester.py`: Downloads Google Fonts and stores them locally. Users can also add their own fonts.
- `font_features.py`: Computes visual features for each font.
- `font_sort.py`: Sorts fonts based on visual similarity and produces a sorted font list and font specimens.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/matevz-kovacic/font-sort.git
2. **Navigate to the project directory:**
   ```bash
   cd font-sort
3. **Install the dependencies:**
   ```bash
   pip install .

## Usage

### 1. Harvest Fonts

Download fonts from Google Fonts or add your own fonts under the `fonts` directory (location of font files in format `/fonts-directory-save-dir/font-name/regular.ttf`).

To download Google Fonts, you need a Google Fonts API key which can be obtained at https://developers.google.com/fonts/docs/developer_api . You can provide this API key via an environment variable or as a command-line argument.

- **Environment Variable:** Set the `GOOGLE_FONTS_API_KEY` environment variable with your API key.
  ```bash
  export GOOGLE_FONTS_API_KEY=your_google_fonts_api_key

- **Command-Line Arguments:**
  ```bash
  python font_harvester.py --api_key your_google_fonts_api_key

#### Command-Line Arguments for `font_harvester.py`

- `--api_key` (str): Google Fonts API key. If not provided, it will be read from the `GOOGLE_FONTS_API_KEY` environment variable.
- `--save_path` (str): Directory to save the fonts. Default is `./fonts`.
- `--styles` (str, nargs='+'): Harvest only certain font styles (e.g., regular, italic, bold). Default is `'regular'`.
- `--subset` (str, nargs='+'): Harvest only subsets of fonts (e.g., latin). Default is `'latin'`.

Example:
```bash
python font_harvester.py --api_key your_google_fonts_api_key --save_path ./fonts --styles regular --subset latin
````

### 2. Compute Font Features

Compute visual features for each font. This step generates feature vectors that are used for sorting fonts based on visual similarity and also computes average glyph density of fonts.

#### Command-Line Arguments for `font_features.py`

- `--font_path` (str): Directory with fonts. Default is `./fonts`.
- `--characters` (str): Characters for font comparisons in each font. Default is `'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@?!'`.
- `--texts` (str, nargs='+'): Array of texts for font comparisons. Default is `'The quick brown fox jumps over the lazy dog'`.
- `--force_features_recompute` (bool): Force features recompute. Default is `True`.

Example:
```bash
python font_features.py --font_path ./fonts --characters 'ABCD' --texts 'Hello World' --force_features_recompute True
```

### 3. Sort Fonts

Sort fonts based on visual similarity and produce a sorted font list and font specimens.

#### Command-Line Arguments for `font_sort.py`

- `--font_path` (str): Directory with fonts. Default is `./fonts`.

Example:
```bash
python font_sort.py --font_path ./fonts
```

## Configuration

System-wide default parameters are stored in `config.py`. You can modify this file to change default settings such as the font directory, font subsets, and styles.


## License

This project is licensed under the MIT License.
