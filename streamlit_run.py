import streamlit as st
import serial_dilution_package as sd
import pandas as pd

# page configs
st.set_page_config(page_title="Serial dilution calculator")

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

st.header("First, set the parameters below")

args = {}

args["leaway_factor"] = st.number_input("Leaway factor (how much the volumes should be enlarged)", min_value=1.0, value=1.1)
args["minimal_volume"] = st.number_input("Minimal volume of pipette", value=2.0)

# give a template
st.header("Second, upload the request form")

st.write("The request form should include two columns named 'concentration' and 'volume'.")
st.write("The first row should be the original stock solution to dilute from. The volume here is the upper bound for this solution.")
st.write("Starting from the second row, the concentrations should be in decreasing order, and the volumes are the requested volumes.")
st.write("An example:")

example_df = pd.DataFrame({
    "concentration": [350, 300, 250, 200],
    "volume": [1000, 200, 250, 200],
})

st.table(example_df)

st.markdown("This template is available [here](https://1drv.ms/u/s!AgkVraR8cgATjLoIOeeZb80hCm2edw?download=1).")

st.write("Now upload your request form")

request_file = st.file_uploader("Upload request csv", type="csv")

if request_file is not None:
    try:
        raw_request_df, request_df, idx_to_concentration, idx_to_volume = \
            sd.load_data_and_process(request_file, args["leaway_factor"])
    except Exception as exp:
        st.error(exp)
        st.stop()

    try:
        sd.check_validity(request_df, args["minimal_volume"])
    except Exception as exp:
        st.error(exp)
        st.stop()

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

    st.header("Solution")
    expander = st.beta_expander("FAQ")
    expander.write("There are five columns in the solution table: 'concentration', 'volume', 'dilution volume', 'buffer volume', and 'from' ")
    expander.write("**Concentration** is exactly the same as in the request form.")
    expander.write("**Volume** is enlarged according to the leaway factor. The volume for the original stock solution is replaced with the actual amount needed.")
    expander.write("**Dilution volume** is the amount to take from the higher-concentration solution.")
    expander.write("**Buffer volume** is the amount of buffer.")
    expander.write("**From** indicates which higher-concentration solution (which row above) to take from.")
    
    st.table(output_df.style.format({
        "concentration": "{:.2f}",
        "volume": "{:.2f}",
        "dilution volume": "{:.2f}",
        "buffer volume": "{:.2f}",
        "from": "{:.0f}"
        }
        ))