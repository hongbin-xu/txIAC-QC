import streamlit as st
import pandas as pd
import numpy as np
 

with st.sidebar:

    qc_type = st.selectbox(label = "QC type", options= ["Year to year", "Audit"], index = 0)
    
    data1 = st.file_uploader("Select Pathway data")
    
    if qc_type == "Audit":
        data2 = st.file_uploader("Select audit data")
    
    perf_index = st.multiselect(label = "Select measures", options= ["IRI", "RUT"])
