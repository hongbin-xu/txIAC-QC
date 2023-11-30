import streamlit as st
import pandas as pd
import numpy as np
 

with st.sidebar:

    qc_type = st.selectbox(label = "QC type", options= ["Year to year", "Audit"], index = 0)
    
    data1_path = st.file_uploader("Select Pathway data")
    data1 = pd.read_csv(data1_path)
    
    if qc_type == "Audit":
        data2_path = st.file_uploader("Select audit data")
        data2 = pd.read_csv(data2_path)
    
    perf_index = st.multiselect(label = "Select measures", options= ["IRI", "RUT"])






# IRI: Left IRI, Right IRI, Avg IRI

# Rut: Left, right, shallow, deep, severe, failure

# Cracks
    # ACP
    # CRCP
    # JCP
    # JRCP


