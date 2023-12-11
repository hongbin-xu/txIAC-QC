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
                            "IRI":['ROUGHNESS (IRI) - LEFT WHEELPATH','ROUGHNESS (IRI) - RIGHT WHEELPATH', 'ROUGHNESS (IRI) - AVERAGE','RIDE UTILITY VALUE'], 
                            # Rut
                            "RUT": ['LEFT - WHEELPATH AVERAGE RUT DEPTH',
                                    'RIGHT - WHEELPATH AVERAGE RUT DEPTH', 
                                    'MAP21 Rutting AVG', 
                                    'ACP RUT AUTO SHALLOW AVG PCT', 'ACP RUT AUTO DEEP AVG PCT', 'ACP RUT AUTO SEVERE PCT', 'ACP RUT AUTO FAILURE PCT',
                                    'ACP RUT SHALLOW UTIL', 'ACP RUT DEEP UTIL',  'ACP RUT SEVERE UTIL'], 

                            "LONGI CRACKS": ['ACP LONGITUDE CRACKING','ACP LONGIT CRACKS UTIL'],

                            "TRANS CRACKS": ['ACP TRANSVERSE CRACKING QTY', 'ACP TRANSVERSE CRACKS UTIL'],

                            "ALLIG CRACKS":['ACP ALLIGATOR CRACKING PCT', 'ACP ALLIG CRK UTIL'],
                            "BLOCK CRACKS":['ACP BLOCK CRACKING PCT', 'ACP BLOCK CRK UTIL'],

                            "PATCHING":['ACP PATCHING PCT', 'ACP PATCHING UTIL'], 

                            "FAILURES":['ACP FAILURE QTY',  'ACP FAILURES UTIL'],

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


# Data loading
@ st.cache_data
def data_load(data1_path, data2_path):
    # File uploading
    data1 = pd.read_csv(data1_path)
    data2 = pd.read_csv(data2_path)#
    return data1, data2

# Function to merge data1 and data2 based on routename and DFO
@st.cache_data
def data_merge(data1 = None, data2 = None, qctype = "Audit", pavtype= "ACP", item_list = None): 
    # Suffixes
    if qctype == "Audit":
        suffixes = ["_Pathway", "_Audit"]
    if qctype == "Year by year": 
        year1, year2 = data1["FISCAL YEAR"].unique(), data2["FISCAL YEAR"].unique()
        suffixes = ["_"+str(year1), "_"+str(year2)]

    # merging data1 and data2
    data = data1.merge(data2, on = "SIGNED HWY AND ROADBED ID", suffixes= suffixes) # merge data
    data = data.loc[(abs(data["BEGINNING DFO"+suffixes[0]]-data["BEGINNING DFO"+suffixes[1]])<0.05)&(abs(data["ENDING DFO"+suffixes[0]]-data["ENDING DFO"+suffixes[1]])<0.05)]

    for item in  item_list:
        if "UTIL" not in item:
            data["d_"+item] = data[item+suffixes[0]] - data[item+suffixes[1]]
    
    return data.reset_index(drop = True)


@st.cache_data
def filter(data= None, item_list=None):
    x =1
    return x



# Summary by district or county
@st.cache_data
def diff_summary(data1 = None, data2 = None, qctype = "Audit", pavtype= "ACP", item_list = None):
    # prefix
    if qctype == "Audit":
        suffixes = ["Pathway", "Audit"]
    if qctype == "Year by year": 
        year1, year2 = data1["FISCAL YEAR"].unique(), data2["FISCAL YEAR"].unique()
        suffixes = [str(year1), str(year2)]

    # county level summary
    county_sum1 = data1.pivot_table(values = item_list, index= ["COUNTY"],aggfunc = "mean").reset_index()
    county_sum1["RATING CYCLE CODE"] = suffixes[0]
    county_sum2 = data2.pivot_table(values = item_list, index= ["COUNTY"],aggfunc = "mean").reset_index()
    county_sum2["RATING CYCLE CODE"] = suffixes[1]
    county_sum = pd.concat([county_sum1, county_sum2]).reset_index(drop=True)
    county_sum = county_sum[["RATING CYCLE CODE"]+item_list].sort_values(by = ["COUNTY", "RATING CYCLE CODE"])

    # District level, true when compare year by year
    if qctype == "Year by year":

        dist_sum1 = data1.pivot_table(values = [x for x in item_list if "UTIL" in x], index= ["FISCAL YEAR"],aggfunc = "mean").reset_index()
        dist_sum2 = data2.pivot_table(values = [x for x in item_list if "UTIL" in x], index= ["FISCAL YEAR"],aggfunc = "mean").reset_index()

        dist_sum = pd.concat([dist_sum1, dist_sum2]).reset_index(drop=True)
        dist_sum = county_sum[["RATING CYCLE CODE"]+item_list].sort_values(by = ["COUNTY", "RATING CYCLE CODE"])
        
        return dist_sum, county_sum
    else:
        return county_sum


# Siderbar
with st.sidebar:
    st.header("PMIS QC")
    st.subheader("I: Load and merge data")
    with st.container():
        # QC type selector
        qc_type = st.selectbox(label = "QC type", options= ["Year by year", "Audit"], index = 1)

        #st.session_state.path1 = st.file_uploader("QC data") 
        st.session_state.path1 = st.file_uploader("QC data") 
        st.session_state.path2 = st.file_uploader("Data to compare") 
        st.write(st.session_state.path1)

        if (st.session_state.path1 is not None)&(st.session_state.path2 is not None):
            st.write("run data loader")
            data1, data2 = data_load(data1_path= st.session_state.path1, data2_path= st.session_state.path2)
            st.write(data1)
        # Pavement type and performance index selector
        pav_type = st.selectbox(label = "Pavement type", options = ["ACP", "CRCP", "JCP"])
        perf_indx = st.multiselect(label = "Select measures", options= perf_indx_list[pav_type].keys())

        # List of items
        item_list = []
        for distress in perf_indx:  # compute difference
            for item in  perf_indx_list[pav_type][distress]:
                item_list = item_list +[item]

        # Data merging
        data = data_merge(data1 = data1, data2 = data2, qctype = qc_type, pavtype= pav_type, item_list = item_list)

    st.subheader("II: Data filter")
    with st.container():


        # thresholds Add function
        data_v1 = data.copy()
        data_v1["flag"] = 0
        thresholds = []
        i = 0
        for item in item_list:
            if "UTIL" not in item_list:
                threshold_temp = st.number_input(label = "d_"+item, value = np.nanpercentile(abs(data["d_"+item]), 95))
                thresholds.append(threshold_temp)
                i+=1
            
        sub_button = st.button("Apply filter")

        # filter add function
        if sub_button:
            i = 0
            for item in item_list:
                if "UTIL" not in item_list:
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

