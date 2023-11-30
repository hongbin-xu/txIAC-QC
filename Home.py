import streamlit as st
import pandas as pd
import numpy as np
 

with st.siderbar():
    
    qc_type = st.selectbox("QC type", ["Year to year", "Audit"], ["Audit"])
    data1 = st.file_uploader("Select Pathway data")
    if qc_type == "Audit":
        data2 = st.file_uploader("Select audit data")
    distress = st.selectbox("Select distress")



