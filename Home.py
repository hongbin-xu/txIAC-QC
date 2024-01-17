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
            'SIGNED HWY AND ROADBED ID', 'DIRECTION','LANE CODE', 'BEGINNING DFO', 'ENDING DFO', 'ATTACHMENT',
            'USER UPDATE', 'DATE UPDATE', 
            'CALCULATED LATITUDE', 'CALCULATED LONGITUDE',
            'DFO FROM', 'DFO TO', 'PMIS HIGHWAY SYSTEM', 'LAST YEAR LANE ERROR']

 
# Data loading
@ st.cache_data
def data_load(data1_path, data2_path, item_list = perf_indx_list["IRI"] + perf_indx_list["RUT"], inv_list = inv_list):
    # File uploading
    data1 = pd.read_csv(data1_path)
    data1['START TIME'] = pd.to_datetime(data1['START TIME'], format='%Y%m%d%H%M%S')
    data2 = pd.read_csv(data2_path)#
    data2['START TIME'] = pd.to_datetime(data2['START TIME'], format='%Y%m%d%H%M%S')
    data1 = data1[inv_list + item_list]
    data2 = data2[inv_list + item_list]
    return data1, data2

# Function to merge data1 and data2 based on routename and DFO
@st.cache_data
def data_merge(data1 = None, data2 = None, qctype = None, inv_list = inv_list, item_list = None): 
   
    # Suffixes
    if qctype == "Audit":
        suffixes = ["_Pathway", "_Audit"]
    if qctype == "Year by year": 
        year1, year2 = data1["FISCAL YEAR"].unique()[0], data2["FISCAL YEAR"].unique()[0]
        suffixes = ["_"+str(year1), "_"+str(year2)]

    # filter based on pavement type code
    data1_v1 = data1[inv_list +item_list].reset_index(drop=True)
    data2_v1 = data2[inv_list +item_list].reset_index(drop=True)
    
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
    return suffixes, data.drop(columns = ["id"+suffixes[1], "id"]).reset_index(drop = True)


@st.cache_data
def pav_filter(data = None, pavtype = None):
    """
    Filters the data based on the specified pavement type.

    Parameters:
    - data: Pandas DataFrame, optional. The input data to be filtered. If not provided, the function will return an empty DataFrame.
    - pavtype: list, optional. A list of pavement type codes to filter the data. If not provided, the function will return the unfiltered data.

    Returns:
    - data_v1: Pandas DataFrame. The filtered data based on the specified pavement type. If no data meets the filter criteria, an empty DataFrame will be returned.
    """
    data_v1 = data.copy()
    if pavtype:
        data_v1 = data_v1.loc[data_v1[[x for x in data_v1.columns if "MODIFIED BROAD PAVEMENT TYPE" in x][0]].isin(pavtype)]
    return data_v1

# filter function
@st.cache_data
def thre_filter(data= None, thresholds = None, qctype = None):
    """
    Filters the data based on the specified thresholds and quality control type.

    Parameters:
    - data: Pandas DataFrame, optional. The input data to be filtered. If not provided, the function will return an empty DataFrame.
    - thresholds: dict, optional. A dictionary containing the thresholds for each key. The keys are the column names in the data DataFrame and the values are tuples with the lower and upper thresholds. If not provided, the function will return the unfiltered data.
    - qctype: str, optional. The quality control type. Possible values are "Audit" and "Year by year". If not provided, the function will return the unfiltered data.

    Returns:
    - data_v1: Pandas DataFrame. The filtered data based on the specified thresholds and quality control type. If no data meets the thresholds, an empty DataFrame will be returned.
    """
    data_v1 = data.copy()
    data_v1["flag"] = 0
    if qctype =="Audit":
        for key in thresholds:
            data_v1.loc[abs(data_v1["diff_"+key])>=thresholds[key][1], "flag"]=1
    if qctype == "Year by year":
        for key in thresholds:
            data_v1.loc[(data_v1["diff_"+key]>=thresholds[key][1])|(data_v1["diff_"+key]<=thresholds[key][0]), "flag"]=1 

    data_v1 = data_v1.loc[data_v1["flag"]==1].reset_index(drop = True)
    return data_v1

# Summary by district or county
@st.cache_data
def diff_summary(data= None, qctype = None, pavtype = None, item_list = None):
    """
        A function that generates a summary of the data based on the provided parameters.

        Parameters:
        - data (pandas.DataFrame): The input data used for generating the summary.
        - qctype (str): The type of quality control, which can be "Audit" or "Year by year".
        - item_list (list): A list of items to include in the summary.

        Returns:
        - If qctype is "Year by year":
        - dist_sum (pandas.DataFrame): The district-level summary of the data.
        - county_sum (pandas.DataFrame): The county-level summary of the data.
        - Otherwise:
        - county_sum (pandas.DataFrame): The county-level summary of the data.
    """
    # prefix
    if qctype == "Audit":
        suffixes = ["Pathway", "Audit"]
    if qctype == "Year by year": 
        years = [x for x in data.columns if "FISCAL YEAR" in x]
        suffixes = [str(years[0][-4:]), str(years[1][-4:])]
    data1 = data.loc[data[[x for x in data.columns if "MODIFIED BROAD PAVEMENT TYPE" in x][0]].isin(pavtype)]
    # county level summary (only matched data records)
    county_sum1 = data1.pivot_table(values = [x+"_"+suffixes[0] for x in item_list], index= ["COUNTY"+"_"+suffixes[0]],aggfunc = "mean").reset_index()
    county_sum1["RATING CYCLE CODE"] = suffixes[0]
    county_sum1.rename(columns = dict(zip([x+"_"+suffixes[0] for x in item_list] +["COUNTY"+"_"+suffixes[0]], item_list+["COUNTY"])), inplace = True)
    county_sum2 = data1.pivot_table(values = [x+"_"+suffixes[1] for x in item_list], index= ["COUNTY"+"_"+suffixes[1]],aggfunc = "mean").reset_index()
    county_sum2["RATING CYCLE CODE"] = suffixes[1]
    county_sum2.rename(columns = dict(zip([x+"_"+suffixes[1] for x in item_list] +["COUNTY"+"_"+suffixes[1]], item_list+["COUNTY"])), inplace = True)

    county_sum = pd.concat([county_sum1, county_sum2]).reset_index(drop=True)
    county_sum = county_sum[["COUNTY", "RATING CYCLE CODE"]+item_list].sort_values(by = ["COUNTY", "RATING CYCLE CODE"])

    # District level, true when compare year by year
    if qctype == "Year by year":
        util_list = [x for x in item_list if "UTIL" in x]
        dist_sum1 = data1.pivot_table(values = [x+"_"+suffixes[0] for x in util_list], index= ["FISCAL YEAR"+"_"+suffixes[0]],aggfunc = "mean").reset_index()
        dist_sum1.rename(columns = dict(zip([x+"_"+suffixes[0] for x in util_list] +["FISCAL YEAR"+"_"+suffixes[0]], util_list+["RATING CYCLE CODE"])), inplace= True)
        dist_sum2 = data1.pivot_table(values = [x+"_"+suffixes[1] for x in util_list], index= ["FISCAL YEAR"+"_"+suffixes[1]],aggfunc = "mean").reset_index()
        dist_sum2.rename(columns = dict(zip([x+"_"+suffixes[1] for x in util_list] +["FISCAL YEAR"+"_"+suffixes[1]], util_list+["RATING CYCLE CODE"])), inplace= True)
        dist_sum = pd.concat([dist_sum1, dist_sum2]).reset_index(drop=True)
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

        # performance index Pavement type selector and generate list of items
        perf_indx = st.multiselect(label = "Select measures", options= perf_indx_list.keys())
        item_list = []
        for distress in perf_indx:
            for item in  perf_indx_list[distress]:
                item_list = item_list +[item]

        # Data loading and merging
        merge_button = st.button("Load and merge data")
        if merge_button&(st.session_state.path1 is not None)&(st.session_state.path2 is not None):
            st.session_state["data1"], st.session_state["data2"] = data_load(data1_path= st.session_state.path1, data2_path= st.session_state.path2)
            st.session_state["suffixes"], st.session_state["data"] = data_merge(data1 = st.session_state["data1"], data2 = st.session_state["data2"], qctype = qc_type,  item_list = item_list)

        # Pavement type selector
        if "IRI" in perf_indx:
            pav_type = st.multiselect(label = "Pavement type", options = pav_list, default = "A - ASPHALTIC CONCRETE PAVEMENT (ACP)")
        else:
            pav_type = st.multiselect(label = "Pavement type", options = ["A - ASPHALTIC CONCRETE PAVEMENT (ACP)"], default = "A - ASPHALTIC CONCRETE PAVEMENT (ACP)")
        if "data" in st.session_state:
            st.session_state["data_v1"] = pav_filter(data= st.session_state["data"], pavtype= pav_type) # Pavement type filter

    st.subheader("II: Data filter")
    with st.container():
        out_type = st.selectbox("Threshold identifier", options=["percentile", "box-style"], key = 1)

        try:
            thresholds = dict()
            if qc_type == "Year by year":        
                if out_type == "percentile":
                    for item in item_list:
                        if "UTIL" not in item:
                            threvals = np.nanpercentile(st.session_state["data"]["diff_"+item].values, [2.5, 97.5])
                            threshold_temp = [st.number_input(label = "diff_"+item+"_lower", value = threvals[0]), st.number_input(label = "diff_"+item+"_upper", value = threvals[1])]
                            thresholds[item] = threshold_temp

                if out_type == "box-style":
                    for item in item_list:
                        if "UTIL" not in item:
                            threvals = np.nanpercentile(st.session_state["data"]["diff_"+item].values, [25, 75])
                            threvals = [threvals[0]-1.5*(threvals[1]-threvals[0]), threvals[1]+1.5*(threvals[1]-threvals[0])]
                            threshold_temp = [st.number_input(label = "diff_"+item+"_lower", value = threvals[0]), st.number_input(label = "diff_"+item+"_upper", value = threvals[1])]
                            thresholds[item] = threshold_temp
            if qc_type =="Audit":
                if out_type == "percentile":
                    for item in item_list:
                        if "UTIL" not in item:
                            threshold_temp = st.number_input(label = "diff_"+item, value = np.nanpercentile(abs(st.session_state["data"]["diff_"+item].values), 95))
                            thresholds[item] = [0, threshold_temp]

                if out_type == "box-style":
                    for item in item_list:
                        if "UTIL" not in item:
                            threvals = np.nanpercentile(abs(st.session_state["data"]["diff_"+item].values), [25, 75])
                            threvals = [threvals[0]-1.5*(threvals[1]-threvals[0]), threvals[1]+1.5*(threvals[1]-threvals[0])]
                            threshold_temp = st.number_input(label = "diff_"+item, value = threvals[1])
                            thresholds[item] = [0, threshold_temp]          
        except:
            pass

        filter_button = st.button("Apply filter")
        # filter add function
        if (filter_button):
            st.session_state["data_v1"]= thre_filter(data= st.session_state["data"], thresholds = thresholds, qctype= qc_type)

# Main
with st.container():
    # District level, true when compare year by year
    if "data" in st.session_state:
        data_sum = diff_summary(data= st.session_state["data"], qctype = qc_type, pavtype = pav_type, item_list = item_list)
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
            list_temp = [x for x in perf_indx_list[p] if "UTIL" not in x]
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
                        #if qc_type == "Audit":
                        #    xdata = abs(st.session_state["data"]["diff_"+item])
                        #if qc_type == "Year by year":
                        xdata = st.session_state["data"]["diff_"+item]

                        hist = go.Histogram(x=xdata, nbinsx=50, showlegend = False)
                        ecdf = px.ecdf(xdata)#, x="d_"+item)
                        ecdf = go.Scatter(x=ecdf._data[0]["x"], y=ecdf._data[0]['y'], mode='lines',  yaxis='y2', showlegend = False)
                        fig.add_trace(hist, row=row, col=col, secondary_y = False)
                        fig.add_trace(ecdf, row=row, col=col, secondary_y = True)
                        #fig.update_layout(row = row, col = col, yaxis_title='Count', yaxis2=dict(title='cdf', overlaying='y', side='right'))
                        fig.update_layout(template="simple_white")
                        fig.update_xaxes(title_text = "diff: "+item, row = row, col = col)
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

    # Container for show distribution of outliers across different variables and location
    with st.container():
        st.subheader("Distribution of outliers")
        #try:
        st.write("0-Location & Matching")
        #fig = make_subplots(rows= 1, cols = 2)

        
        #st.plotly_chart(fig, use_container_width= True)
        
        # count of the filtered data based on SIGNED HWY AND ROADBED ID
        st.markdown("- SIGNED HWY AND ROADBED ID")
        df_temp = st.session_state["data_v1"].groupby(by = "SIGNED HWY AND ROADBED ID"+st.session_state["suffixes"][0]).size().reset_index(name = "count").sort_values(by = "count", ascending = False)
        fig = px.bar(df_temp, x = "SIGNED HWY AND ROADBED ID"+st.session_state["suffixes"][0], y = "count")
        st.plotly_chart(fig, use_container_width= True)

        # Lane number
        st.write("2-LANE NUMBER")

        


        st.write("3-DIRECTION")     


        st.write("4-COUNTY")


        st.write("5-START TIME")


        st.write("6-VEHICLE ID")


        st.write("7-AVERAGE SPEED")


        st.write("8-RIDE COMMENT CODE")


        st.write("9-ACP RUT AUTO COMMENT CODE")


        st.write("10-INTERFACE FLAG")


        st.write("11-LANE WIDTH")

        #st.map(st.session_state["data_v1"], latitude= "LATITUDE BEGIN_2024", longitude=	"LONGITUDE BEGIN_2024", size=20)

        #except:
        #    pass


#Audit

#Year by year

# """ 'FISCAL YEAR', 
# 'SIGNED HWY AND ROADBED ID', # all in count 
# 'LANE NUMBER',  # count summary for consistent lane number or inconsistent
# 'DIRECTION', # count summary for consistent direction or inconsistent
# 'BEGINNING DFO', # Overlapping 
# 'ENDING DFO', # 
# 'COUNTY', # count summary

# 'START TIME', # time differnce between start time and end time
# 'VEHICLE ID', # count for both txdot and pmis
# #'OPERATOR NAME', # count for both txdot and pmis
# 'AVERAGE SPEED', # speed difference txdot and pmis
# #'MODIFIED BROAD PAVEMENT TYPE', # all in count
# 'RIDE COMMENT CODE', # 
# 'ACP RUT AUTO COMMENT CODE', 
# #'RATER NAME1', 
# 'INTERFACE FLAG', 
# #'RATER NAME2',
# #'DISTRESS COMMENT CODE',
# 'LANE WIDTH',
# #'DETAILED PVMNT TYPE ROAD LIFE', """
