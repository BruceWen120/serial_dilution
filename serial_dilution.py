import numpy as np
import pandas as pd
import argparse, os

def parse_args():
    parser = argparse.ArgumentParser(description="Automated serial dilution calculation")
    parser.add_argument("file_path", type=str, help="path to the input csv file")
    parser.add_argument("--minimal_volume", default=2, type=float, help="the minimal volume for the pipette")
    parser.add_argument("--leaway_factor", default=1.5, type=float, help="factor by which the volumes are expanded to provide leaway")
    return parser.parse_args()

def check_stock_solution(idx_to_concentration, idx_to_volume, vmin):
    min_concentrations = set()
    max_concentrations = set()

    for j, v_j in idx_to_volume.items():
        if j == 0:
            continue
        min_concentrations.add((v_j / (v_j - args.minimal_volume)) * idx_to_concentration[j])
        max_concentrations.add((v_j / args.minimal_volume) * idx_to_concentration[j])
        
    if idx_to_concentration[0] < max(min_concentrations):
        # too low
        raise Exception(f"original stock solution's concentration needs to be at least {max(min_concentrations):.2f}")
        
    if max(min_concentrations) < min(max_concentrations):
        # one stock solution can cover all
        if idx_to_concentration[0] > min(max_concentrations):
            raise Exception(f"original stock solution needs to be diluted to {max(min_concentrations):.2f} to {min(max_concentrations):.2f}")
    else:
        # need multiple stock solutions to dilute from
        # see if two can cover all
        raise Exception("one stock solution is not able to cover all the ranges")

if __name__ == "__main__":
    args = parse_args()

    raw_request_df = pd.read_csv(args.file_path)
    assert raw_request_df.columns.to_list() == ["concentration", "volume"]

    request_df = raw_request_df.copy()
    request_df["volume"][1:] = args.leaway_factor * raw_request_df["volume"][1:]

    idx_to_concentration = dict(zip(request_df.index, request_df["concentration"]))
    idx_to_volume = dict(zip(request_df.index, request_df["volume"]))

    # validity check
    sum_series = request_df["concentration"] * request_df["volume"]
    assert sum_series[0] > sum_series[1:].sum(), "not enough solution"
    assert all(request_df["volume"] > 2 * args.minimal_volume)

    # check for diluting the stock solution
    check_stock_solution(idx_to_concentration, idx_to_volume, args.minimal_volume)

    # initialize
    j_to_i = {}
    v_need_dict = {idx: raw_request_df["volume"].iloc[idx] if idx != 0 else 0 for idx in range(raw_request_df.shape[0])}
    v_dilute_dict = {}
    v_buffer_dict = {}

    for j in range(request_df.shape[0] - 1, 0, -1):
        if (idx_to_volume[j] / (idx_to_volume[j] - args.minimal_volume)) * idx_to_concentration[j] > idx_to_concentration[0]:
            # j's concentration too large, fail
            raise Exception(f"concentration at {j}-th row is too large ({idx_to_concentration[j]})")
        elif (idx_to_volume[j] / args.minimal_volume) * idx_to_concentration[j] < idx_to_concentration[0]:
            # j's concentration too small for the original stock solution, search for newer ones
            for i in range(1, j):
                if (idx_to_volume[j] / (idx_to_volume[j] - args.minimal_volume)) * idx_to_concentration[j] \
                    > idx_to_concentration[i]:
                    # j's concentration too large for i, fail
                    raise Exception(f"concentration at {j}-th row is too large ({idx_to_concentration[j]})")
                elif (idx_to_volume[j] / args.minimal_volume) * idx_to_concentration[j] > idx_to_concentration[i]:
                    j_to_i[j] = i
                    break
            if i == j - 1:
                raise Exception(f"concentration at {j}-th row is too small ({idx_to_concentration[j]})")
        else:
            # best case scenario, can dilute from original stock solution
            j_to_i[j] = 0
        v_need_dict[j_to_i[j]] += (idx_to_concentration[j] / idx_to_concentration[j_to_i[j]]) * idx_to_volume[j]
        if v_need_dict[j_to_i[j]] > idx_to_volume[j_to_i[j]]:
            # the volume needed for i-th row is larger than the requested volume even after adjusting, fail
            raise Exception(f"volume needed for {j_to_i[j]}-th row is too large ({v_need_dict[j_to_i[j]]}), try requesting more")
        v_dilute_dict[j] = (idx_to_concentration[j] / idx_to_concentration[j_to_i[j]]) * idx_to_volume[j]
        v_buffer_dict[j] = ((idx_to_concentration[j_to_i[j]] - idx_to_concentration[j]) \
                            / idx_to_concentration[j_to_i[j]]) * idx_to_volume[j]

    # output
    output_df = pd.concat([request_df, pd.DataFrame(columns=["dilution volume", "buffer volume", "from"])], sort=False)
    for j, i in j_to_i.items():
        output_df.at[j, "from"] = i
        output_df.at[j, "buffer volume"] = v_buffer_dict[j]
        output_df.at[j, "dilution volume"] = v_dilute_dict[j]
    output_df.at[0, "volume"] = v_need_dict[0]

    # save to file
    output_path = os.path.splitext(args.file_path)[0] + "_output.csv"
    output_df.to_csv(output_path)