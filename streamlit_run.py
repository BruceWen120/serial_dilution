import streamlit as st
import serial_dilution_package as sd

st.title('Serial dilution calculator')

st.write("This tool automates serial dilution calculation. ")
st.write(
    "Given the concentration of the available stock solution, the new concentrations needed, "
    "and their respective volumes, it calculate, for each request, "
    "which higher-concentration solution to dilute from, the corresponding volume, and the buffer volume.")
st.write(
    "It can add some leaway volume, account for the minimal volume allowed for the pipette, "
    "and when necessary find intermediate solutions to bootstrap from.")
st.write(
    "It does not handle all edge cases and exceptions (yet), "
    "but it will provide instructive feedback when it fails to find a solution.")

args = {}

args["leaway_factor"] = st.number_input("Leaway factor", min_value=1.0, value=1.1)
args["minimal_volume"] = st.number_input("Minimal volume of pipette", value=2.0)

request_file = st.file_uploader("Upload request csv", type="csv")

if request_file is not None:
    raw_request_df, request_df, idx_to_concentration, idx_to_volume = \
        sd.load_data_and_process(request_file, args["leaway_factor"])

    sd.check_validity(request_df, args["minimal_volume"])

    try:
        sd.check_stock_solution(idx_to_concentration, idx_to_volume, args["minimal_volume"])
    except Exception as exp:
        st.error(exp)
        st.stop()

    try:
        output_df = sd.get_dilutions(raw_request_df, request_df, idx_to_concentration, \
            idx_to_volume, args["minimal_volume"])
    except Exception as exp:
        st.error(exp)
        st.stop()

    st.dataframe(output_df.style.format("{:.2f}"))