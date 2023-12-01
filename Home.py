import streamlit as st
import pandas as pd
import numpy as np
 


perf_index_list = {"ACP":
                        {   
                            "IRI":['ROUGHNESS (IRI) - LEFT WHEELPATH','ROUGHNESS (IRI) - RIGHT WHEELPATH', 'ROUGHNESS (IRI) - AVERAGE', 'RIDE LI', 'RIDE UTILITY VALUE'], 
                            # Rut
                            "RUT": ['LEFT - WHEELPATH AVERAGE RUT DEPTH',
                                    'RIGHT - WHEELPATH AVERAGE RUT DEPTH', 
                                    'MAP21 Rutting AVG',

                                    'LEFT - WHEELPATH NO RUT', 'LEFT - WHEELPATH SHALLOW RUT',  'LEFT - WHEELPATH DEEP RUT', 'LEFT - WHEELPATH SEVERE RUT', 'LEFT - WHEELPATH FAILURE RUT',
                                    'RIGHT - WHEELPATH NO RUT','RIGHT - WHEELPATH SHALLOW RUT', 'RIGHT - WHEELPATH DEEP RUT', 'RIGHT - WHEELPATH SEVERE RUT', 'RIGHT - WHEELPATH FAILURE RUT', 
                                    
                                    'ACP RUT AUTO SHALLOW AVG PCT', 'ACP RUT AUTO DEEP AVG PCT', 'ACP RUT AUTO SEVERE PCT', 'ACP RUT AUTO FAILURE PCT', 

                                    'ACP RUT SHALLOW LI', 'ACP RUT DEEP LI', 'ACP RUT SEVERE LI', 

                                    'ACP RUT SHALLOW UTIL', 'ACP RUT DEEP UTIL',  'ACP RUT SEVERE UTIL'], 

                            "LONGI CRACKS": ['ACP LONGITUDINAL CRACK UNSEALED', 'ACP LONGITUDINAL CRACK SEALED', 'ACP LONGITUDE CRACKING', 
                                            'ACP LONGITUDINAL CRACKING UNSEALED PCT', 'ACP LONGITUDINAL CRACKING SEALED PCT', 'ACP LONGIT CRACKS LI', 'ACP LONGIT CRACKS UTIL'],

                            "TRANS CRACKS": ['ACP TRANSVERSE CRACK UNSEALED', 'ACP TRANSVERSE CRACK SEALED', 'ACP TRANSVERSE CRACKING QTY', 'ACP TRANSVERSE CRACKING UNSEALED PCT', 
                                            'ACP TRANSVERSE CRACKING SEALED PCT', 'ACP TRANSVERSE CRACKS LI', 'ACP TRANSVERSE CRACKS UTIL'],

                            "ALLIG CRACKS":['ACP ALLIGATOR CRACKING UNSEALED', 'ACP ALLIGATOR CRACKING SEALED', 'ACP ALLIGATOR CRACKING PCT', 'ACP ALLIGATOR CRACKING UNSEALED PCT', 
                                            'ACP ALLIGATOR CRACKING SEALED PCT',  'ACP ALLIG CRK LI', 'ACP ALLIG CRK UTIL'],
                            "BLOCK CRACKS":['ACP BLOCK CRACKING UNSEALED', 'ACP BLOCK CRACKING SEALED', 'ACP BLOCK CRACKING PCT', 'ACP BLOCK CRACKING UNSEALED PCT',
                                            'ACP BLOCK CRACKING SEALED PCT', 'ACP BLOCK CRK LI', 'ACP BLOCK CRK UTIL'],

                            "PATCHING":['ACP PATCHING MEASURED', 'ACP PATCHING PCT', 'ACP PATCHING LI', 'ACP PATCHING UTIL'], 

                            "FAILURES":['ACP FAILURE QTY', 'ACP FAILURES LI',  'ACP FAILURES UTIL'],

                            "RAVELING": ['ACP RAVELING','ACP RAVELING CODE', 'ACP FLUSHING','ACP FLUSHING CODE'],

                            "Other":['ACP RAVELING','ACP RAVELING CODE', 'ACP FLUSHING','ACP FLUSHING CODE', 'ACP PERCENT AREA CRACKED', 'POTHOLE']
                        },
                    "CRCP": 
                        { 
                            "SPALLED CRACKS":['CRCP SPALLED CRACKS QTY', 'CRCP SPALLED CRACKS LI', 'CRCP SPALLED CRACKS UTIL'],
                            "PUNCHOUT":['CRCP PUNCHOUT QTY', 'CRCP PUNCHOUTS LI','CRCP PUNCHOUTS UTIL'],
                            "PCC PATCHES":['CRCP PCC PATCHES QTY','CRCP PCC PATCHES LI','CRCP PCC PATCHES UTIL'],
                            "ACP PATCHES":['CRCP ACP PATCHES QTY', 'CRCP ACP PATCHES LI', 'CRCP ACP PATCHES UTIL'],
                            "Other":['CRCP LONGITUDINAL CRACKING MEASURED', 'AVERAGE CRACK SPACING','CRCP PERCENT AREA CRACKED','CRCP LONGITUDE CRACKING PCT']
                        },
                    "JCP": 
                        { 
                            "FAILED JOINTS": ['JCP FAILED JNTS CRACKS QTY', 'JCP FAILED JOINTS LI', 'JCP FAILED JOINTS UTIL'],
                            "FAILURES":['JCP FAILURES QTY','JCP FAILURES LI','JCP FAILURES UTIL'],
                            "SHATTERED SLABS": ['JCP SHATTERED SLABS QTY', 'JCP SHATTERED SLABS LI', 'JCP SHATTERED SLABS UTIL'],
                            "SLABS WITH LONGI CRACKS": ['JCP SLABS WITH LONGITUDINAL CRACKS', 'JCP SLABS WITH LONG CRACKS LI', 'JCP SLABS WITH LONG CRACKS UTIL'],
                            "PCC PATCHES": ['JCP PCC PATCHES QTY', 'JCP PCC PATCHES LI','JCP PCC PATCHES UTIL'],
                            "Other": ['JCP PERCENT OF SLABS WITH CRACKS',  'JCP CRACK PERCENT PCT', 'CALCULATED LENGTH', 'JCP APPARENT JOINT SPACING',
                                      'MAP21 Faulting RWP AVG','MAP21 Faulting Condition Category', 'FAULTING MEASURE']
                        }
                    "Other index":['MAP21 Cracking Percent', 'MAP21 Cracking Condition Category']
                }





 







@st.function
def data_merge(data1, data2, qctype = "Audit"): 
    if qctype == "Audit":
        data = data1.merge(data2, on = "SIGNED HWY AND ROADBED ID", suffixes= ["Pathway", "Audit"])
        data = data.loc[(abs(data["BEGINNING DFOPathway"]-data["BEGINNING DFOAudit"])<0.05)&(abs(data["ENDING DFOPathway"]-data["ENDING DFOAudit"])<0.05)]
    if qctype == "Year to year":
        data1
    return data



# Steamlit main tab
def main():
    with st.sidebar:

        qc_type = st.selectbox(label = "QC type", options= ["Year to year", "Audit"], index = 1)
        
        data1_path = st.file_uploader("Select Pathway data")
        if "data1_path" in globals():
            data1 = pd.read_csv(data1_path)
        
        if qc_type == "Audit":
            data2_path = st.file_uploader("Select audit data")
            if "data2_path" in globals():
                data2 = pd.read_csv(data2_path)
        
        perf_index = st.multiselect(label = "Select measures", options= ["IRI", "RUT"])



if __name__ == "__main__":
    main()
