import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


st.set_page_config(layout="wide", 
                   page_title='PMIS QC', 
                   menu_items={
                       'Get help': "mailto:hongbinxu@utexas.edu",
                       'About': "Developed and maintained by Hongbin Xu",
                   })

# List of distresses
perf_indx_list = {"ACP":
                        {   "Aggregated": ['DISTRESS SCORE','RIDE SCORE', 'CONDITION SCORE'],
                            "IRI":['ROUGHNESS (IRI) - LEFT WHEELPATH','ROUGHNESS (IRI) - RIGHT WHEELPATH', 'ROUGHNESS (IRI) - AVERAGE'], 
                            # Rut
                            "RUT": ['LEFT - WHEELPATH AVERAGE RUT DEPTH',
                                    'RIGHT - WHEELPATH AVERAGE RUT DEPTH', 
                                    'MAP21 Rutting AVG', 
                                    'ACP RUT AUTO SHALLOW AVG PCT', 'ACP RUT AUTO DEEP AVG PCT', 'ACP RUT AUTO SEVERE PCT', 'ACP RUT AUTO FAILURE PCT'], 

                            "LONGI CRACKS": ['ACP LONGITUDE CRACKING'],

                            "TRANS CRACKS": ['ACP TRANSVERSE CRACKING QTY'],

                            "ALLIG CRACKS":['ACP ALLIGATOR CRACKING PCT'],
                            "BLOCK CRACKS":['ACP BLOCK CRACKING PCT'],

                            "PATCHING":['ACP PATCHING PCT'], 

                            "FAILURES":['ACP FAILURE QTY'],

                            "RAVELING": ['ACP RAVELING'], 
                            "FLUSHING": ['ACP FLUSHING'],

                            "ACP Other":['ACP PERCENT AREA CRACKED', 'POTHOLE']
                        },

                    "CRCP": 
                        {   "Aggregated": ['DISTRESS SCORE','RIDE SCORE', 'CONDITION SCORE'],
                            "SPALLED CRACKS":['CRCP SPALLED CRACKS QTY'],
                            "PUNCHOUT":['CRCP PUNCHOUT QTY'],
                            "PCC PATCHES":['CRCP PCC PATCHES QTY'],
                            "ACP PATCHES":['CRCP ACP PATCHES QTY'],
                            "CRCP Other":['CRCP LONGITUDINAL CRACKING MEASURED', 'AVERAGE CRACK SPACING','CRCP PERCENT AREA CRACKED','CRCP LONGITUDE CRACKING PCT']
                        },
                    "JCP": 
                        {   "Aggregated": ['DISTRESS SCORE','RIDE SCORE', 'CONDITION SCORE'],
                            "FAILED JOINTS": ['JCP FAILED JNTS CRACKS QTY'],
                            "FAILURES":['JCP FAILURES QTY'],
                            "SHATTERED SLABS": ['JCP SHATTERED SLABS QTY'],
                            "SLABS WITH LONGI CRACKS": ['JCP SLABS WITH LONGITUDINAL CRACKS'],
                            "PCC PATCHES": ['JCP PCC PATCHES QTY'],
                            "JCP Other": ['JCP PERCENT OF SLABS WITH CRACKS',  'JCP CRACK PERCENT PCT', 'CALCULATED LENGTH', 'JCP APPARENT JOINT SPACING',
                                      'MAP21 Faulting RWP AVG','MAP21 Faulting Condition Category', 'FAULTING MEASURE']
                        }
                }


# Function to merge data1 and data2 based on routename and DFO
@st.cache_data
def data_merge(data1 = None, data2 = None, qctype = "Audit", pavtype= "ACP", perf_indx = None): 
    # Suffixes
    if qctype == "Audit":
        suffixes = ["_Pathway", "_Audit"]
    if qctype == "Year by year": 
        year1, year2 = data1["FISCAL YEAR"].unique(), data2["FISCAL YEAR"].unique()
        suffixes = ["_"+str(year1), "_"+str(year2)]

    # merging data1 and data2
    data = data1.merge(data2, on = "SIGNED HWY AND ROADBED ID", suffixes= suffixes) # merge data
    data = data.loc[(abs(data["BEGINNING DFOPathway"]-data["BEGINNING DFOAudit"])<0.05)&(abs(data["ENDING DFOPathway"]-data["ENDING DFOAudit"])<0.05)]
    
    for distress in perf_indx:  # compute difference
        for item in  perf_indx_list[pavtype][distress]:
            data["d_"+item] = data[item+"_"+suffixes[0]] - data[item+"_"+suffixes[1]]
    
    return data.reset_index(drop = True)


try:
    # Siderbar
    with st.sidebar:
        st.header("PMIS QC")
        st.subheader("I: Load and merge data")
        with st.container():
            qc_type = st.selectbox(label = "QC type", options= ["Year by year", "Audit"], index = 1)

            data1_path = st.file_uploader("QC data") 
            if "data1_path" in globals():
                data1 = pd.read_csv(data1_path)

            data2_path = st.file_uploader("Data to compare")
            if "data2_path" in globals():
                data2 = pd.read_csv(data2_path)#

            pav_type = st.selectbox(label = "Pavement type", options = ["ACP", "CRCP", "JCP"])
            perf_indx = st.multiselect(label = "Select measures", options= perf_indx_list[pav_type].keys())

            data = data_merge(data1 = data1, data2 = data2, qctype = qc_type, pavtype= pav_type, perf_indx = perf_indx)
            st.write(data)

        st.subheader("II: Data filter")
        with st.container():
            data_v1 = data.copy()
            data_v1["flag"] = 0
            thresholds = []
            for p in perf_indx:            
                i = 0
                for item in perf_indx_list[pav_type][p]:
                    threshold_temp = st.number_input(label = str(i)+"_d_"+item, value = np.nanpercentile(abs(data["d_"+item]), 95))
                    thresholds.append(threshold_temp)
                    #st.write(np.quantile(abs(data["d_"+item]), 0.95))

                    i+=1
            sub_button = st.button("Apply filter")
            if sub_button:
                for p in perf_indx:            
                    i = 0
                    for item in perf_indx_list[pav_type][p]:
                        data_v1.loc[abs(data_v1["d_"+item])>=thresholds[i], "flag"]=1
                        i+=1
                data_v1 = data_v1.loc[data_v1["flag"]==1].reset_index(drop = True)

    # Main
    with st.container():
        for p in perf_indx:
            rows = int(math.ceil(len(perf_indx_list[pav_type][p])/3))
            st.subheader(p + " (Pathway - Audit) " + "distribution")
            fig = make_subplots(rows= rows, cols = 3,
                                specs=[[{"secondary_y": True}]*3]*rows)#,
                                #horizontal_spacing=0.1,
                                #vertical_spacing = .5)

            i = 0
            for item in perf_indx_list[pav_type][p]:
                row = i//3+1
                col = i%3+1

                # Create histogram
                #fig = px.histogram(data, x = "d_"+item)

                # Create ECDF
                #ecdf = px.ecdf(data, x="d_"+item)
                #fig.add_scatter(x=ecdf._data[0]["x"], y=ecdf._data[0]['y'], mode='lines', name='cdf', yaxis='y2')
                #
                # Update layout
                #fig.update_layout(yaxis_title='Count', yaxis2=dict(title='cdf', overlaying='y', side='right'))
                #st.plotly_chart(fig)
                hist = go.Histogram(x=abs(data["d_"+item]), nbinsx=30, showlegend = False)
                ecdf = px.ecdf(abs(data["d_"+item]))#, x="d_"+item)
                ecdf = go.Scatter(x=ecdf._data[0]["x"], y=ecdf._data[0]['y'], mode='lines',  yaxis='y2', showlegend = False)
                fig.add_trace(hist, row=row, col=col, secondary_y = False)
                fig.add_trace(ecdf, row=row, col=col, secondary_y = True)
                #fig.update_layout(row = row, col = col, yaxis_title='Count', yaxis2=dict(title='cdf', overlaying='y', side='right'))
                fig.update_xaxes(title_text = "d_"+item, row = row, col = col)
                fig.update_yaxes(title_text="count", row=row, col=col, secondary_y=False)
                fig.update_yaxes(title_text='cdf', row=row, col=col, secondary_y=True)
                i+=1
            
            fig.update_layout(height=400*rows)
            st.plotly_chart(fig, use_container_width= True)


    with st.container():
        st.subheader("Filtered data")
        st.write("Number of rows: "+ str(data_v1.shape[0]))
        st.write(data_v1)
        st.download_button(label="Download filtered data", data=data_v1.to_csv().encode('utf-8'), file_name="filtered.csv", mime = "csv")
except:
    pass
