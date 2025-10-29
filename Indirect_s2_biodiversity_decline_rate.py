import argparse
import os
import shutil
import time
import pandas as pd
from glob import glob
import natcap.invest.habitat_quality

def prepare_threats_table(template_path, output_path, lulc_cur_path, lulc_fut_path,
                          urban_threat_name, rural_threat_name):
    """
    Creates a threats CSV file for a specific InVEST run from a template.

    Args:
        template_path (str): Path to the template threats CSV file.
        output_path (str): Path to save the generated threats CSV file.
        lulc_cur_path (str): Path to the current LULC raster.
        lulc_fut_path (str): Path to the future LULC raster.
        urban_threat_name (str): The filename of the urban threat raster.
        rural_threat_name (str): The filename of the rural threat raster.
    """
    try:
        threats_df = pd.read_csv(template_path)
        
        # This assumes the template has specific THREAT names to be replaced.
        # Example: THREAT column has 'urban' and 'rural'
        if 'urban' in threats_df['THREAT'].values:
            threats_df.loc[threats_df['THREAT'] == 'urban', 'PATH'] = urban_threat_name
        if 'rural' in threats_df['THREAT'].values:
            threats_df.loc[threats_df['THREAT'] == 'rural', 'PATH'] = rural_threat_name

        # A more generic approach if threat names in CSV match raster names
        # for index, row in threats_df.iterrows():
        #     threat_name = row['THREAT']
        #     if 'urban' in threat_name:
        #          threats_df.loc[index, 'PATH'] = urban_threat_name
        #     elif 'rural' in threat_name:
        #          threats_df.loc[index, 'PATH'] = rural_threat_name
            
        threats_df.to_csv(output_path, index=False)
        return True
    except Exception as e:
        print(f"Error preparing threats table: {e}")
        return False

def run_habitat_quality_analysis(base_dir, lulc_dir, threats_template, sensitivity_table, half_saturation, n_workers):
    """
    Runs the InVEST Habitat Quality model for a set of tiled LULC rasters.

    Args:
        base_dir (str): The main workspace directory for InVEST.
        lulc_dir (str): Subdirectory containing the tiled LULC raster files.
        threats_template (str): Path to the template threats CSV file.
        sensitivity_table (str): Path to the sensitivity CSV file.
        half_saturation (float): Half-saturation constant for the model.
        n_workers (int): Number of worker processes to use.
    """
    start_time = time.time()
    
    # Find all 'current' LULC files to process
    search_pattern = os.path.join(lulc_dir, '*_2000_lulc.tif')
    lulc_files = glob(search_pattern)
    
    if not lulc_files:
        print(f"Warning: No LULC files found with pattern: {search_pattern}")
        return

    print(f"Found {len(lulc_files)} LULC files to process.")

    for lulc_cur_path in lulc_files:
        try:
            filename_base = os.path.basename(lulc_cur_path)
            print(f"\n--- Processing: {filename_base} ---")
            
            # --- 1. Define corresponding file paths ---
            lulc_fut_path = lulc_cur_path.replace('_2000_lulc.tif', '_2020_lulc.tif')
            urban_threat_cur_path = lulc_cur_path.replace('_2000_lulc.tif', '_2000_urban.tif')
            rural_threat_cur_path = lulc_cur_path.replace('_2000_lulc.tif', '_2000_rural.tif')

            if not os.path.exists(lulc_fut_path):
                print(f"Warning: Future LULC not found for {lulc_cur_path}. Skipping.")
                continue

            # --- 2. Prepare the threats table for this specific run ---
            run_threats_path = os.path.join(base_dir, 'threats_for_run.csv')
            prepare_threats_table(
                template_path=threats_template,
                output_path=run_threats_path,
                lulc_cur_path=lulc_cur_path,
                lulc_fut_path=lulc_fut_path,
                # Assuming threat rasters are in the same directory as LULC tiles
                urban_threat_name=os.path.basename(urban_threat_cur_path),
                rural_threat_name=os.path.basename(rural_threat_cur_path)
            )

            # --- 3. Set up InVEST model arguments ---
            args = {
                'workspace_dir': base_dir,
                'lulc_cur_path': lulc_cur_path,
                'lulc_fut_path': lulc_fut_path,
                'threats_table_path': run_threats_path,
                'sensitivity_table_path': sensitivity_table,
                'half_saturation_constant': str(half_saturation), # InVEST requires string
                'n_workers': n_workers
            }

            # --- 4. Execute the model ---
            print("Executing InVEST Habitat Quality model...")
            natcap.invest.habitat_quality.execute(args)

            # --- 5. Rename output files for clarity ---
            print("Renaming output files...")
            deg_sum_c_old = os.path.join(base_dir, "quality_c.tif")
            deg_sum_c_new = os.path.join(base_dir, f"quality_c_{filename_base}")
            if os.path.exists(deg_sum_c_old):
                os.rename(deg_sum_c_old, deg_sum_c_new)

            deg_sum_f_old = os.path.join(base_dir, "quality_f.tif")
            deg_sum_f_new = os.path.join(base_dir, f"quality_f_{filename_base.replace('2000', '2020')}")
            if os.path.exists(deg_sum_f_old):
                os.rename(deg_sum_f_old, deg_sum_f_new)
            
            # --- 6. Clean up intermediate files ---
            intermediate_dir = os.path.join(base_dir, 'intermediate')
            if os.path.exists(intermediate_dir):
                print("Cleaning intermediate files...")
                shutil.rmtree(intermediate_dir)
            
            print(f"--- Finished processing: {filename_base} ---")

        except Exception as e:
            print(f"An error occurred while processing {lulc_cur_path}: {e}")
            continue

    total_seconds = time.time() - start_time
    print(f'\nTotal Time Taken for all files: {time.strftime("%H:%M:%S", time.gmtime(total_seconds))}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run the InVEST Habitat Quality model in batch for tiled rasters.'
    )
    parser.add_argument(
        '--workspace', required=True,
        help='Main InVEST workspace directory. Outputs will be saved here.'
    )
    parser.add_argument(
        '--lulc_dir', required=True,
        help='Directory containing the tiled LULC, urban, and rural rasters.'
    )
    parser.add_argument(
        '--threats_template', required=True,
        help='Path to the template threats CSV file. The "PATH" column will be dynamically filled.'
    )
    parser.add_argument(
        '--sensitivity_table', required=True,
        help='Path to the sensitivity CSV file.'
    )
    parser.add_argument(
        '--half_saturation', type=float, default=0.5,
        help='Half-saturation constant for the model (k). Default is 0.5.'
    )
    parser.add_argument(
        '--n_workers', type=int, default=-1,
        help='Number of worker processes for InVEST. Default is -1 (all available cores).'
    )

    args = parser.parse_args()

    run_habitat_quality_analysis(
        base_dir=args.workspace,
        lulc_dir=args.lulc_dir,
        threats_template=args.threats_template,
        sensitivity_table=args.sensitivity_table,
        half_saturation=args.half_saturation,
        n_workers=args.n_workers
    )