import argparse
import os
import time
import rasterio
from rasterio.windows import Window
import numpy as np

def split_raster_by_grid(input_raster, output_dir, grid_size_km=1000, overlap_km=25):
    """
    Splits a large raster file into smaller tiles based on a specified grid size.

    This function divides a GeoTIFF raster into a grid of smaller rasters,
    with an optional overlap between adjacent tiles. Tiles that contain only
    NoData values are skipped.

    Args:
        input_raster (str): Path to the input GeoTIFF file.
        output_dir (str): Directory to save the output tiled GeoTIFF files.
        grid_size_km (float, optional): The desired width and height of each
                                        grid cell in kilometers. Defaults to 1000.
        overlap_km (float, optional): The overlap between adjacent tiles in
                                      kilometers. Defaults to 25.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory created at: {output_dir}")

        with rasterio.open(input_raster) as src:
            # Get raster metadata
            width = src.width
            height = src.height
            transform = src.transform
            nodata_value = src.nodata
            
            # Use X and Y resolution from the transform. Handle potential rotation.
            resolution_x = transform.a
            resolution_y = abs(transform.e)
            
            if resolution_x == 0 or resolution_y == 0:
                raise ValueError("Raster resolution cannot be zero.")

            # Calculate grid and overlap sizes in pixels
            grid_size_x = int(grid_size_km * 1000 / resolution_x)
            grid_size_y = int(grid_size_km * 1000 / resolution_y)
            overlap_x = int(overlap_km * 1000 / resolution_x)
            overlap_y = int(overlap_km * 1000 / resolution_y)
            
            print(f"Grid size in pixels: {grid_size_x} x {grid_size_y}")
            print(f"Overlap size in pixels: {overlap_x} x {overlap_y}")

            # Calculate the number of tiles in each dimension
            step_x = grid_size_x - overlap_x
            step_y = grid_size_y - overlap_y
            
            if step_x <= 0 or step_y <= 0:
                raise ValueError("Grid size must be larger than overlap size.")
                
            num_grids_x = (width - 1) // step_x + 1
            num_grids_y = (height - 1) // step_y + 1
            
            print(f"Splitting raster into {num_grids_x} x {num_grids_y} tiles...")

            # Get the base name of the input file to use in output names
            base_name = os.path.splitext(os.path.basename(input_raster))[0]

            # Iterate over each grid cell and export it as a separate GeoTIFF file
            for i in range(num_grids_x):
                for j in range(num_grids_y):
                    # Calculate the window for the current tile, including overlap
                    x_start = i * step_x
                    y_start = j * step_y
                    
                    # Define window dimensions, ensuring they don't exceed raster bounds
                    window_width = min(grid_size_x, width - x_start)
                    window_height = min(grid_size_y, height - y_start)
                    
                    window = Window(x_start, y_start, window_width, window_height)
                    
                    # Read the data within the window
                    data = src.read(window=window)

                    # Check if the tile is entirely NoData
                    if nodata_value is not None and np.all(data == nodata_value):
                        print(f"Skipping tile {i}_{j} as it is entirely NoData.")
                        continue
                    
                    # Get the geotransform for the current window
                    window_transform = src.window_transform(window)
                    
                    # Create a descriptive output filename
                    output_file = os.path.join(output_dir, f"{base_name}_tile_{i}_{j}.tif")
                    
                    # Write the window's image data to a new GeoTIFF file
                    profile = src.profile.copy()
                    profile.update({
                        'height': window_height,
                        'width': window_width,
                        'transform': window_transform,
                        'compress': 'lzw',
                        'nodata': nodata_value
                    })
                    
                    with rasterio.open(output_file, 'w', **profile) as dst:
                        dst.write(data)
                    
                    print(f"Exported {output_file}")
                    
        print("\nRaster splitting completed successfully.")

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_raster}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    # --- Command Line Argument Parser ---
    parser = argparse.ArgumentParser(
        description='Split a large GeoTIFF raster into smaller, overlapping tiles.'
    )
    parser.add_argument(
        '--input_raster', 
        type=str, 
        required=True, 
        help='Path to the input GeoTIFF raster file.'
    )
    parser.add_argument(
        '--output_dir', 
        type=str, 
        required=True, 
        help='Directory to save the output tiles.'
    )
    parser.add_argument(
        '--grid_size_km', 
        type=float, 
        default=1000.0, 
        help='The side length of each square tile in kilometers. Default is 1000.'
    )
    parser.add_argument(
        '--overlap_km', 
        type=float, 
        default=25.0, 
        help='The overlap between adjacent tiles in kilometers. Default is 25.'
    )
    
    args = parser.parse_args()

    # --- Execute the Function ---
    start_time = time.time()
    
    split_raster_by_grid(
        input_raster=args.input_raster, 
        output_dir=args.output_dir,
        grid_size_km=args.grid_size_km,
        overlap_km=args.overlap_km
    )

    end_time = time.time()
    seconds = end_time - start_time
    print(f'\nTotal Time Taken: {time.strftime("%H:%M:%S", time.gmtime(seconds))}')