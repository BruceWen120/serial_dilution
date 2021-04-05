import numpy as np
import pandas as pd

def load_data_and_process(file_path, leaway_factor):
    raw_request_df = pd.read_csv(file_path)
    assert raw_request_df.columns.to_list() == ["concentration", "volume"]

    request_df = raw_request_df.copy()
    request_df["volume"][1:] = leaway_factor * raw_request_df["volume"][1:]

    idx_to_concentration = dict(zip(request_df.index, request_df["concentration"]))
    idx_to_volume = dict(zip(request_df.index, request_df["volume"]))

    return raw_request_df, request_df, idx_to_concentration, idx_to_volume

def check_validity(request_df, vmin):
    sum_series = request_df["concentration"] * request_df["volume"]
    assert sum_series[0] > sum_series[1:].sum(), "not enough solution"
    assert all(request_df["volume"] > 2 * vmin)

def check_stock_solution(idx_to_concentration, idx_to_volume, vmin):
    min_concentrations = set()
    max_concentrations = set()

    for j, v_j in idx_to_volume.items():
        if j == 0:
            continue
        min_concentrations.add((v_j / (v_j - vmin)) * idx_to_concentration[j])
        max_concentrations.add((v_j / vmin) * idx_to_concentration[j])
        
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
        # raise Exception("one stock solution is not able to cover all the ranges")
        pass

def get_dilutions(raw_request_df, request_df, idx_to_concentration, idx_to_volume, vmin):
    # initialize
    j_to_i = {}
    v_need_dict = {idx: raw_request_df["volume"].iloc[idx] if idx != 0 else 0 for idx in range(raw_request_df.shape[0])}
    v_dilute_dict = {}
    v_buffer_dict = {}

    # calculate
    for j in range(request_df.shape[0] - 1, 0, -1):
        if (idx_to_volume[j] / (idx_to_volume[j] - vmin)) * idx_to_concentration[j] \
            > idx_to_concentration[0]:
            # j's concentration too large, fail
            raise Exception(f"concentration request {idx_to_concentration[j]} is too large to be diluted from the original stock solution")
        elif (idx_to_volume[j] / vmin) * idx_to_concentration[j] < idx_to_concentration[0]:
            # j's concentration too small for the original stock solution, search for newer ones
            succeed = False
            lower_bound = (idx_to_volume[j] / (idx_to_volume[j] - vmin)) * idx_to_concentration[j]
            upper_bound = (idx_to_volume[j] / vmin) * idx_to_concentration[j]
            for i in range(1, j):
                if (idx_to_concentration[i] > lower_bound) and \
                        (idx_to_concentration[i] < upper_bound):
                    j_to_i[j] = i
                    succeed = True
                    break
            if not succeed:
                raise Exception(f"concentration request {idx_to_concentration[j]} can only be diluted from a solution in range {lower_bound:.2f} to {upper_bound:.2f}, which is not available")
        else:
            # best case scenario, can dilute from original stock solution
            j_to_i[j] = 0
        v_need_dict[j_to_i[j]] += (idx_to_concentration[j] / idx_to_concentration[j_to_i[j]]) * idx_to_volume[j]
        if v_need_dict[j_to_i[j]] > idx_to_volume[j_to_i[j]]:
            # the volume needed for i-th row is larger than the requested volume even after adjusting, fail
            raise Exception(f"volume needed for request {idx_to_concentration[j_to_i[j]]} is too large ({v_need_dict[j_to_i[j]]}), try requesting more")
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

    return output_df