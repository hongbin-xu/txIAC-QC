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

# Pavement list code 
pav_list = ["A - ASPHALTIC CONCRETE PAVEMENT (ACP)", "C - CONTINUOUSLY REINFORCED CONCRETE PAVEMENT (CRCP)", "J - JOINTED CONCRETE PAVEMENT (JCP)"]

# List of distresses
perf_indx_list = {  "IRI":['ROUGHNESS (IRI) - LEFT WHEELPATH','ROUGHNESS (IRI) - RIGHT WHEELPATH', 'ROUGHNESS (IRI) - AVERAGE','RIDE UTILITY VALUE'],
                    
                    # Rut
                    "RUT": ['LEFT - WHEELPATH AVERAGE RUT DEPTH',
                            'RIGHT - WHEELPATH AVERAGE RUT DEPTH', 
                            'MAP21 Rutting AVG', 
                            'ACP RUT AUTO SHALLOW AVG PCT', 'ACP RUT AUTO DEEP AVG PCT', 'ACP RUT AUTO SEVERE PCT', 'ACP RUT AUTO FAILURE PCT',
                            'ACP RUT SHALLOW UTIL', 'ACP RUT DEEP UTIL',  'ACP RUT SEVERE UTIL']
                }

# Information list contains informaiton about location and measurement information
inv_list = ['FISCAL YEAR', 'HEADER TYPE', 'START TIME', 'VEHICLE ID', 'VEHICLE VIN',
            'CERTIFICATION DATE', 'TTI CERTIFICATION CODE', 'OPERATOR NAME',
            'SOFTWARE VERSION', 'MAXIMUM SPEED', 'MINIMUM SPEED', 'AVERAGE SPEED',
            'OPERATOR COMMENT', 'RATING CYCLE CODE', 'FILE NAME',
            'RESPONSIBLE DISTRICT', 'COUNTY', 'RESPONSIBLE MAINTENANCE SECTION',
            'LANE NUMBER', 'LATITUDE BEGIN', 'LONGITUDE BEGIN', 'ELEVATION BEGIN',
            'BEARING BEGIN', 'LATITUDE END', 'LONGITUDE END', 'ELEVATION END',
            'BEARING END', 'BROAD PAVEMENT TYPE', 'MODIFIED BROAD PAVEMENT TYPE',
            'BROAD PAVEMENT TYPE SHAPEFILE', 'RIDE COMMENT CODE',
            'ACP RUT AUTO COMMENT CODE', 'RATER NAME1', 'INTERFACE FLAG', 'RATER NAME2',
            'DISTRESS COMMENT CODE', 'LANE WIDTH',
            'DETAILED PVMNT TYPE ROAD LIFE',
            'DETAILED PVMNT TYPE VISUAL CODE', 
            'SIGNED HWY AND ROADBED ID', 'LANE CODE', 'BEGINNING DFO', 'ENDING DFO', 'ATTACHMENT',
            'USER UPDATE', 'DATE UPDATE', 
            'CALCULATED LATITUDE', 'CALCULATED LONGITUDE',
            'DFO FROM', 'DFO TO', 'PMIS HIGHWAY SYSTEM']

# Data loading
@ st.cache_data
def data_load(data1_path, data2_path):
    # File uploading
    data1 = pd.read_csv(data1_path)
    data2 = pd.read_csv(data2_path)#
    return data1, data2

# Function to merge data1 and data2 based on routename and DFO
@st.cache_data
def data_merge(data1 = None, data2 = None, qctype = None, pavtype = None, inv_list = inv_list, item_list = None): 
   
    # Suffixes
    if qctype == "Audit":
        suffixes = ["_Pathway", "_Audit"]
    if qctype == "Year by year": 
        year1, year2 = data1["FISCAL YEAR"].unique()[0], data2["FISCAL YEAR"].unique()[0]
        suffixes = ["_"+str(year1), "_"+str(year2)]

    # filter based on pavement type code
    data1_v1 = data1.loc[data1["MODIFIED BROAD PAVEMENT TYPE"].isin(pavtype), inv_list +item_list].reset_index(drop=True)
    data2_v1 = data2.loc[data2["MODIFIED BROAD PAVEMENT TYPE"].isin(pavtype), inv_list +item_list].reset_index(drop=True)
    
    # merging data1 and data2
    data1_v1 = data1_v1.loc[data1_v1["COUNTY"].isin(data2_v1["COUNTY"])].reset_index(drop = True)
    data1_v1["id"]= np.arange(data1_v1.shape[0])
    data2_v1["id"] = np.arange(data2_v1.shape[0])

    id_match = data1_v1[["SIGNED HWY AND ROADBED ID", "COUNTY", "BEGINNING DFO", "ENDING DFO", "id"]].merge(data2_v1[["SIGNED HWY AND ROADBED ID", "COUNTY", "BEGINNING DFO", "ENDING DFO", "id"]],
                                                                                                            how ="left", 
                                                                                                            on = ["SIGNED HWY AND ROADBED ID", "COUNTY"],
                                                                                                            suffixes= suffixes)
    id_match = id_match.loc[(abs(id_match["BEGINNING DFO"+suffixes[0]]-id_match["BEGINNING DFO"+suffixes[1]])<0.05)&(abs(id_match["ENDING DFO"+suffixes[0]]-id_match["ENDING DFO"+suffixes[1]])<0.05)]

    # id_2024, id_2023, id
    data = id_match[["id"+suffixes[0], "id"+suffixes[1]]].merge(data1_v1, how = "left", left_on = "id"+suffixes[0], right_on = "id") # merge data
    data = data.drop(columns = ["id"+suffixes[0], "id"]).merge(data2_v1, how = "left", left_on = "id"+suffixes[1], right_on = "id", suffixes = suffixes) # merge data

    for item in  item_list:
        if "UTIL" not in item:
            data["diff_"+item] = data[item+suffixes[0]] - data[item+suffixes[1]]
    return data.drop(columns = ["id"+suffixes[1], "id"]).reset_index(drop = True)

# filter function
@st.cache_data
def filter(data= None, thresholds = None, item_list=None):
    data_v1 = data.copy()
    data_v1["flag"] = 0
    i = 0
    for item in item_list:
        if "UTIL" not in item:
            data_v1.loc[abs(data_v1["diff_"+item])>=thresholds[i], "flag"]=1
            i+=1
    data_v1 = data_v1.loc[data_v1["flag"]==1].reset_index(drop = True)
    return data_v1

# Summary by district or county
@st.cache_data
def diff_summary(data1 = None, data2 = None, qctype = "Audit", item_list = None):
    # prefix
    if qctype == "Audit":
        suffixes = ["Pathway", "Audit"]
    if qctype == "Year by year": 
        year1, year2 = data1["FISCAL YEAR"].unique()[0], data2["FISCAL YEAR"].unique()[0]
        suffixes = [str(year1), str(year2)]

    # county level summary
    county_sum1 = data1.pivot_table(values = item_list, index= ["COUNTY"],aggfunc = "mean").reset_index()
    county_sum1["RATING CYCLE CODE"] = suffixes[0]
    county_sum2 = data2.pivot_table(values = item_list, index= ["COUNTY"],aggfunc = "mean").reset_index()
    county_sum2["RATING CYCLE CODE"] = suffixes[1]
    county_sum = pd.concat([county_sum1, county_sum2]).reset_index(drop=True)
    county_sum = county_sum[["COUNTY", "RATING CYCLE CODE"]+item_list].sort_values(by = ["COUNTY", "RATING CYCLE CODE"])

    # District level, true when compare year by year
    if qctype == "Year by year":
        util_list = [x for x in item_list if "UTIL" in x]
        dist_sum1 = data1.pivot_table(values = util_list, index= ["FISCAL YEAR"],aggfunc = "mean").reset_index()
        dist_sum2 = data2.pivot_table(values = util_list, index= ["FISCAL YEAR"],aggfunc = "mean").reset_index()
        dist_sum = pd.concat([dist_sum1, dist_sum2]).reset_index(drop=True)
        dist_sum.rename(columns = {"FISCAL YEAR": "RATING CYCLE CODE"}, inplace= True)

        dist_sum = dist_sum[["RATING CYCLE CODE"]+util_list].sort_values(by = ["RATING CYCLE CODE"])
        
        return dist_sum, county_sum
    else:
        return county_sum

# Siderbar
with st.sidebar:
    st.header("PMIS QC")
    st.subheader("I: Data Loading and Merging")
    with st.container():
        # QC type selector
        qc_type = st.selectbox(label = "QC type", options= ["Year by year", "Audit"], index = 1)

        #st.session_state.path1 = st.file_uploader("QC data") 
        st.session_state.path1 = st.file_uploader("QC data", type ="csv") 
        st.session_state.path2 = st.file_uploader("Data to compare", type ="csv")         

        # Pavement type and performance index selector
        perf_indx = st.multiselect(label = "Select measures", options= perf_indx_list.keys())
        pav_type = st.multiselect(label = "Pavement type", options = pav_list, default = "A - ASPHALTIC CONCRETE PAVEMENT (ACP)")

        # List of items
        item_list = []
        for distress in perf_indx:  # compute difference
            for item in  perf_indx_list[pav_type][distress]:
                item_list = item_list +[item]

        # Data merging
        merge_button = st.button("Load and merge data")
        if merge_button&(st.session_state.path1 is not None)&(st.session_state.path2 is not None):
            st.session_state["data1"], st.session_state["data2"] = data_load(data1_path= st.session_state.path1, data2_path= st.session_state.path2)
            st.session_state["data1"] = st.session_state["data1"][inv_list + item_list]
            st.session_state["data2"] = st.session_state["data2"][inv_list + item_list]
            st.session_state["data"] = data_merge(data1 = st.session_state["data1"], data2 = st.session_state["data2"], qctype = qc_type, pavtype= pav_type, item_list = item_list)
            st.session_state["data_v1"] = st.session_state["data"].copy()

    st.subheader("II: Data filter")
    with st.container():
        try:        
            thresholds = []
            i = 0
            for item in item_list:
                if "UTIL" not in item:
                    threshold_temp = st.number_input(label = "diff_"+item, value = np.nanpercentile(abs(st.session_state["data"]["diff_"+item].values), 95))
                    thresholds.append(threshold_temp)
                    i+=1
        except:
            pass
        filter_button = st.button("Apply filter")
        # filter add function
        if (filter_button):
            st.session_state["data_v1"]= filter(data= st.session_state["data"], thresholds = thresholds, item_list=item_list)

# Main
# Summary
with st.container():
    # Summary
    if qc_type == "Audit":
        suffixes = ["Pathway", "Audit"]
    if (qc_type == "Year by year")&("data1" in st.session_state)&("data2" in st.session_state): 
        year1, year2 = st.session_state["data1"]["FISCAL YEAR"].unique()[0], st.session_state["data2"]["FISCAL YEAR"].unique()[0]
        suffixes = [str(year1), str(year2)]
    # District level, true when compare year by year
        data_sum = diff_summary(data1 = st.session_state["data1"], data2 = st.session_state["data2"], qctype = qc_type, pavtype= pav_type, item_list = item_list)
        if qc_type =="Audit":
            st.subheader("County summary")
            st.write(data_sum)
        if qc_type == "Year by year":
            st.subheader("District summary")
            st.write(data_sum[0])
            st.subheader("County summary")
            st.write(data_sum[1])

if "data" in st.session_state:

    # Plot
    with st.container():
        st.subheader("Distribution Plots")
        for p in perf_indx:
            list_temp = [x for x in perf_indx_list[pav_type][p] if "UTIL" not in x]
            rows = int(math.ceil(len(list_temp)/3))
            st.write(p + " (Pathway - Audit) " + "distribution")
            fig = make_subplots(rows= rows, cols = 3,
                                specs=[[{"secondary_y": True}]*3]*rows)

            i = 0
            for item in list_temp:
                if "UTIL" not in item:
                    row = i//3+1
                    col = i%3+1
                    try:
                        xdata = abs(st.session_state["data"]["diff_"+item])
                        hist = go.Histogram(x=abs(st.session_state["data"]["diff_"+item]), nbinsx=30, showlegend = False)
                        ecdf = px.ecdf(abs(st.session_state["data"]["diff_"+item]))#, x="d_"+item)
                        ecdf = go.Scatter(x=ecdf._data[0]["x"], y=ecdf._data[0]['y'], mode='lines',  yaxis='y2', showlegend = False)
                        fig.add_trace(hist, row=row, col=col, secondary_y = False)
                        fig.add_trace(ecdf, row=row, col=col, secondary_y = True)
                        #fig.update_layout(row = row, col = col, yaxis_title='Count', yaxis2=dict(title='cdf', overlaying='y', side='right'))
                        fig.update_xaxes(title_text = "Abs diff: "+item, row = row, col = col)
                        fig.update_yaxes(title_text="count", row=row, col=col, secondary_y=False)
                        fig.update_yaxes(title_text='cdf', row=row, col=col, secondary_y=True)
                    except:
                        break
                    i+=1
                
            fig.update_layout(height=400*rows)
            st.plotly_chart(fig, use_container_width= True)

    # Filtered data
    with st.container():
        st.subheader("Filtered data")
        try:
            st.write("Number of rows: "+ str(st.session_state["data_v1"].shape[0]))
            st.write(st.session_state["data_v1"])
            st.downloadiff_button(label="Download filtered data", data=st.session_state["data_v1"].to_csv().encode('utf-8'), file_name="filtered.csv", mime = "csv")
        except:
            pass

