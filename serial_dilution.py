import numpy as np
import pandas as pd
import argparse, os

import serial_dilution_package as sd

def parse_args():
    parser = argparse.ArgumentParser(description="Automated serial dilution calculation")
    parser.add_argument("file_path", type=str, help="path to the input csv file")
    parser.add_argument("--minimal_volume", default=2, type=float, help="the minimal volume for the pipette")
    parser.add_argument("--leaway_factor", default=1.5, type=float, help="factor by which the volumes are expanded to provide leaway")
    parser.add_argument("--no_file_saving", action="store_true", help="results not saved to file")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    raw_request_df, request_df, idx_to_concentration, idx_to_volume = \
        sd.load_data_and_process(args.file_path, args.leaway_factor)

    sd.check_validity(request_df, args.minimal_volume)
    sd.check_stock_solution(idx_to_concentration, idx_to_volume, args.minimal_volume)

    output_df = sd.get_dilutions(raw_request_df, request_df, idx_to_concentration, idx_to_volume, args.minimal_volume)

    # save to file
    if args.no_file_saving:
        print(output_df)
    else:
        output_path = os.path.splitext(args.file_path)[0] + "_output.csv"
        output_df.to_csv(output_path)