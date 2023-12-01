import streamlit as st
import pandas as pd
import numpy as np
 


@st.function
def merge(data1, data2, perf_index, qctype = "Audit")
    data_combined = data1.merge(data2, how = , by = )








def main():
    with st.sidebar:

        qc_type = st.selectbox(label = "QC type", options= ["Year to year", "Audit"], index = 1)
        
        data1_path = st.file_uploader("Select Pathway data")
        if data1_path.exists():
            data1 = pd.read_csv(data1_path)
        
        if qc_type == "Audit":
            data2_path = st.file_uploader("Select audit data")
            if data2_path.exists():
                data2 = pd.read_csv(data2_path)
        
        perf_index = st.multiselect(label = "Select measures", options= ["IRI", "RUT"])




# IRI: Left IRI, Right IRI, Avg IRI

# Rut: Left, right, shallow, deep, severe, failure

# Cracks
    # ACP
    # CRCP
    # JCP
    # JRCP


