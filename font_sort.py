import argparse
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from config import DEFAULT_FONT_PATH


def load_fonts(font_directory):
    """Load feature vectors and densities for all fonts in the specified directory."""
    feature_files = []
    ttf_files = []
    font_names = []
    font_densities = []

    for root, _, files in os.walk(font_directory):
        for file in files:
            if file.endswith('.ttf'):
                ttf_file_path = os.path.join(root, file)
                feature_file_path = ttf_file_path + '.features.npy'
                density_file_path = ttf_file_path + '.density'

                if os.path.exists(feature_file_path) and os.path.exists(density_file_path):
                    font_name = f"{os.path.basename(root)}_{os.path.splitext(file)[0]}"
                    feature_files.append(feature_file_path)
                    ttf_files.append(ttf_file_path)
                    font_names.append(font_name)

                    with open(density_file_path, 'r') as f:
                        font_density = float(f.readline().strip())
                    font_densities.append(font_density)

    return feature_files, ttf_files, font_names, font_densities


def save_font_list(font_names, ordered_indices, list_path):
    with open(list_path, 'w') as f:
        for idx in ordered_indices:
            f.write(font_names[idx] + '\n')


def filter_fonts_by_groups(densities, ordered_indices, thresholds):

    groups = {i: [] for i in range(len(thresholds) + 1)}

    for idx in ordered_indices:
        density = densities[idx]
        group_found = False
        for i, threshold in enumerate(thresholds):
            if density <= threshold:
                groups[i].append(idx)
                group_found = True
                break
        if not group_found:
            groups[len(thresholds)].append(idx)

    return groups


def create_image_with_text(ttf_files, font_names, font_indices, text, image_path, display_font_name):
    # Try to find the specified font name in the font_names list
    if display_font_name in font_names:
        name_font_index = font_names.index(display_font_name)
    else:
        # If not found, choose the median font index
        name_font_index = font_indices[len(font_indices) // 2]

    # Get the font for displaying font names
    display_font = ImageFont.truetype(ttf_files[name_font_index], 20)

    # Create a new image
    num_fonts = len(font_indices)
    line_height = 50  # Height of each line
    image_height = num_fonts * line_height  # Total height of the image
    image_width = 1200  # Width of the image
    image = Image.new('RGB', (image_width, image_height), 'white')
    draw = ImageDraw.Draw(image)

    # Draw the text for each font
    for i, idx in enumerate(font_indices):
        font_path = ttf_files[idx]
        specimen_font = ImageFont.truetype(font_path, 20)
        y_position = i * line_height
        draw.text((10, y_position), font_names[idx].removesuffix('_regular'), font=display_font, fill='black')
        draw.text((400, y_position), text, font=specimen_font, fill='black')

    # Save the image
    image.save(image_path)


def closest_fonts(font_name, font_names, distance_matrix, n=5):
    """Display the names of the n closest fonts to the given font_name."""
    try:
        index = font_names.index(font_name)
    except ValueError:
        print(f"Font name '{font_name}' not found in the list of font names.")
        return

    # Get distances for the specified font
    distances = distance_matrix[index]

    # Get indices of the closest fonts (excluding the font itself)
    closest_indices = np.argsort(distances)[1:n+1]

    # Display the names of the closest fonts
    closest_font_names = [font_names[i] for i in closest_indices]
    print(f"The {n} closest fonts to '{font_name}' are:")
    for name in closest_font_names:
        print(name)


def path_length(ordered_indices, distance_matrix):
    """Compute the length of the path given the ordered indices and the distance matrix."""
    total_length = 0
    for i in range(len(ordered_indices) - 1):
        total_length += distance_matrix[ordered_indices[i], ordered_indices[i + 1]]
    return total_length


def load_features(file_path):
    """Load feature vectors from a .npy file."""
    try:
        features = np.load(file_path)
        return features
    except Exception as e:
        print(f"Error loading features from {file_path}: {e}")
        return None


def euclidean_distance(features1, features2):
    return np.linalg.norm(features1 - features2)


def calculate_distance_matrix(feature_files):
    """Calculate the pairwise cosine distance matrix by loading features as needed."""
    num_fonts = len(feature_files)
    distance_matrix = np.zeros((num_fonts, num_fonts))
    for i in range(num_fonts):
        print(f'Calculating font distance matrix {i}/{num_fonts}', end='\r', flush=True)

        features_i = load_features(feature_files[i])
        for j in range(i + 1, num_fonts):
            features_j = load_features(feature_files[j])
            dist = euclidean_distance(features_i, features_j)
            distance_matrix[i, j] = dist
            distance_matrix[j, i] = dist

    print('Calculating font distance matrix completed')
    return distance_matrix


def optimized_font_path(distance_matrix):
    """Create a font path starting with the most distant pair of fonts and extending with the closest neighbor."""
    def closest_neighbor(current_font):
        closest_font = None
        min_distance = float('inf')
        for neighbor in remaining_fonts:
            if distance_matrix[current_font, neighbor] < min_distance:
                min_distance = distance_matrix[current_font, neighbor]
                closest_font = neighbor
        return closest_font

    num_fonts = len(distance_matrix)
    remaining_fonts = set(range(num_fonts))

    # Find the most distant pair of fonts
    max_distance = -1
    start_font = None

    for i in range(num_fonts):
        for j in range(i + 1, num_fonts):
            if distance_matrix[i, j] > max_distance:
                max_distance = distance_matrix[i, j]
                start_font = i

    # Initialize the path with one of the most distant fonts
    path = [start_font]
    remaining_fonts.remove(start_font)

    # Extend the path with the closest neighbor of the current end node
    current_font = start_font
    while remaining_fonts:
        print(f'Optimizing font path {100 *  (num_fonts - len(remaining_fonts)) // num_fonts} %', end='\r', flush=True)

        next_font = closest_neighbor(current_font)
        path.append(next_font)
        remaining_fonts.remove(next_font)
        current_font = next_font

    print(f'Optimizing font path completed')
    return path


def improve_font_path(ordered_indices, distance_matrix):
    """Try to move each font to another position to shorten the path."""

    def calculate_path_length(path):
        return sum(distance_matrix[path[i], path[i + 1]] for i in range(len(path) - 1))

    best_path = ordered_indices[:]
    best_length = calculate_path_length(best_path)
    improved = True

    while improved:
        improved = False
        for i in range(len(best_path)):
            for j in range(len(best_path)):
                if i == j:
                    continue
                new_path = best_path[:i] + best_path[i + 1:]
                new_path.insert(j, best_path[i])
                new_length = calculate_path_length(new_path)
                if new_length < best_length:
                    best_path = new_path
                    best_length = new_length
                    improved = True
                    print(f'Trying to improve solution: moved font from position {i} to {j}, new best path length: {best_length:.2f}        ', end='\r', flush=True)
                    break  # Break out of the inner loop to restart the process with the new best path

    return best_path


def save_data(path, font_names, font_densities, ttf_files):
    save_font_list(font_names, path, './ordered_fonts_list.txt')

    # Calculate density groups of fonts
    glyph_density_groups = np.percentile(font_densities, [25, 50, 75])

    # Filter fonts by groups in quartiles
    groups = filter_fonts_by_groups(font_densities, path, glyph_density_groups)
    sample_file_name = ['featherweight.png', 'thin.png', 'regular.png', 'bold.png']

    # Create images for each quartile
    text = "The quick brown fox jumps over the lazy dog"
    for i in range(len(glyph_density_groups) + 1):
        group_indices = groups[i]
        if group_indices:
            create_image_with_text(ttf_files, font_names, group_indices, text, f'font_samples_{i + 1}_{sample_file_name[i]}', 'Open Sans_regular')
        else:
            print(f"No fonts in group {i + 1}")

    image_path = 'font_list_samples_all.png'
    create_image_with_text(ttf_files, font_names, path, text, image_path, 'Open Sans_regular')
    print('font specimen files saved')


def main():

    parser = argparse.ArgumentParser(description='Sort fonts based in visual similarity')
    parser.add_argument('--font_path', type=str, default=DEFAULT_FONT_PATH, help='Directory with fonts.')
    args = parser.parse_args()

    feature_files, ttf_files, font_names, font_densities = load_fonts(args.font_path)
    print('Loaded font names, files, and densities')

    distance_matrix = calculate_distance_matrix(feature_files)
    print('\nDistance matrix computed')

    path = optimized_font_path(distance_matrix)
    print(f'Font path computed. Final path length: {path_length(path, distance_matrix):.2f}')

    path = improve_font_path(path, distance_matrix)
    print(f'\nImproved font path computed. Final path length: {path_length(path, distance_matrix):.2f}')

    save_data(path, font_names, font_densities, ttf_files)


if __name__ == "__main__":
    main()
