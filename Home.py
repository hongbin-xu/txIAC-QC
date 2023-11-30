import streamlit as st
import pandas as pd
import numpy as np
 

with st.sidebar:

    st.subheader("QC type")
    qc_type = st.selectbox(label = "QC type", options= ["Year to year", "Audit"], index = 0, label_visibility= "hidden")
    
    st.subheader("Select Pathway data")
    data1 = st.file_uploader("Select Pathway data", label_visibility= "hidden")
    
    if qc_type == "Audit":
        st.subheader("Select audit data")
        data2 = st.file_uploader("Select audit data", label_visibility= "hidden")
    
    st.subheader("Performance measures")
    perf_index = st.multiselect(label = "Select measures", options= ["IRI", "RUT"], label_visibility= "hidden")
