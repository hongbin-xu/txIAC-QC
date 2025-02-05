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
inv_list = ['FISCAL YEAR', 'SIGNED HWY AND ROADBED ID', 'BEGINNING DFO', 'ENDING DFO',
            'RESPONSIBLE DISTRICT', 'COUNTY','LANE NUMBER', 
            'HEADER TYPE', 'START TIME', 'VEHICLE ID', 'VEHICLE VIN',
            'CERTIFICATION DATE', 'TTI CERTIFICATION CODE', 'OPERATOR NAME',
            'SOFTWARE VERSION', 'MAXIMUM SPEED', 'MINIMUM SPEED', 'AVERAGE SPEED',
            'OPERATOR COMMENT', 'RATING CYCLE CODE', 'FILE NAME',
            'RESPONSIBLE MAINTENANCE SECTION',
            #'LATITUDE BEGIN', 'LONGITUDE BEGIN', 'ELEVATION BEGIN',
            #'BEARING BEGIN', 'LATITUDE END', 'LONGITUDE END', 'ELEVATION END',
            #'BEARING END', 
            'BROAD PAVEMENT TYPE', 'MODIFIED BROAD PAVEMENT TYPE',
            'BROAD PAVEMENT TYPE SHAPEFILE', 'RIDE COMMENT CODE',
            "RIDE SCORE TRAFFIC LEVEL",
            'ACP RUT AUTO COMMENT CODE', 'RATER NAME1', 'INTERFACE FLAG', 'RATER NAME2',
            'DISTRESS COMMENT CODE', 'LANE WIDTH',
            'DETAILED PVMNT TYPE ROAD LIFE',
            'DETAILED PVMNT TYPE VISUAL CODE', 
             'DIRECTION','LANE CODE','ATTACHMENT',
            'USER UPDATE', 'DATE UPDATE', 
            #'CALCULATED LATITUDE', 'CALCULATED LONGITUDE',
            #'DFO FROM', 'DFO TO', 
            'PMIS HIGHWAY SYSTEM', 'LAST YEAR LANE ERROR']

def check_password():
    """Returns `True` if the user had a correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and st.session_state["password"]
            == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store username + password
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct.
        return True

# Data loading
@ st.cache_data
def data_load(data1_path, data2_path, item_list = None):

    heading_cols = ['FISCAL YEAR', 'SIGNED HWY AND ROADBED ID', 'BEGINNING DFO', 'ENDING DFO', 'RESPONSIBLE DISTRICT', 'COUNTY'] + item_list

    # File uploading
    data1 = pd.read_csv(data1_path)
    data1['START TIME'] = pd.to_datetime(data1['START TIME'], format='%Y%m%d%H%M%S')
    data1["SECTION LENGTH"] = abs(data1["BEGINNING DFO"]-data1["ENDING DFO"])
    data2 = pd.read_csv(data2_path)#
    data2['START TIME'] = pd.to_datetime(data2['START TIME'], format='%Y%m%d%H%M%S')
    data2["SECTION LENGTH"] = abs(data2["BEGINNING DFO"]-data2["ENDING DFO"])
    data1 = data1[heading_cols+ [x for x in data1.columns if x not in heading_cols]]
    data2 = data2[heading_cols+ [x for x in data2.columns if x not in heading_cols]]
    return data1, data2

# Function to merge data1 and data2 based on routename and DFO
@st.cache_data
def data_merge(data1 = None, data2 = None, qctype = None, item_list = None): 
   
    # Suffixes
    if qctype == "Audit":
        suffixes = ["_Pathway", "_Audit"]
    if qctype == "Year by year": 
        year1, year2 = data1["FISCAL YEAR"].unique()[0], data2["FISCAL YEAR"].unique()[0]
        suffixes = ["_"+str(year1), "_"+str(year2)]

    # filter based on pavement type code
    data1_v1 = data1.copy()
    data2_v1 = data2.copy()
    
    # merging data1 and data2
    data1_v1 = data1_v1.loc[data1_v1["COUNTY"].isin(data2_v1["COUNTY"])].reset_index(drop = True)
    data1_v1["idm"]= np.arange(data1_v1.shape[0])
    data2_v1["idm"] = np.arange(data2_v1.shape[0])

    id_match = data1_v1[["SIGNED HWY AND ROADBED ID", "COUNTY", "BEGINNING DFO", "ENDING DFO", "idm"]].merge(data2_v1[["SIGNED HWY AND ROADBED ID", "COUNTY", "BEGINNING DFO", "ENDING DFO", "idm"]],
                                                                                                            how ="left", 
                                                                                                            on = ["SIGNED HWY AND ROADBED ID", "COUNTY"],
                                                                                                            suffixes= suffixes)
    id_match = id_match.loc[(abs(id_match["BEGINNING DFO"+suffixes[0]]-id_match["BEGINNING DFO"+suffixes[1]])<0.05)&(abs(id_match["ENDING DFO"+suffixes[0]]-id_match["ENDING DFO"+suffixes[1]])<0.05)]

    # id_2024, id_2023, id
    data = id_match[["idm"+suffixes[0], "idm"+suffixes[1]]].merge(data1_v1, how = "left", left_on = "idm"+suffixes[0], right_on = "idm") # merge data
    data = data.drop(columns = ["idm"+suffixes[0], "idm"]).merge(data2_v1, how = "left", left_on = "idm"+suffixes[1], right_on = "idm", suffixes = suffixes) # merge data

    for item in  item_list:
        data["diff_"+item] = data[item+suffixes[0]].values - data[item+suffixes[1]].values
    return suffixes, data.drop(columns = ["idm"+suffixes[1], "idm"]).reset_index(drop = True)


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
def diff_summary(data= None, perf_indx= None, qctype = None, item_list = None):
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
        suffixes = ["_Pathway", "_Audit"]
    if qctype == "Year by year": 
        years = [x for x in data.columns if "FISCAL YEAR" in x]
        suffixes = ["_"+str(years[0][-4:]), "_"+str(years[1][-4:])]
    data1 = data.copy()
    data1["sec_len1"] = data1["BEGINNING DFO"+suffixes[0]] - data1["ENDING DFO"+suffixes[0]]
    data1["sec_len2"] = data1["BEGINNING DFO"+suffixes[1]] - data1["ENDING DFO"+suffixes[1]]

    # county level summary (only matched data records)
    county_sum1 = data1.pivot_table(values = [x+suffixes[0] for x in item_list], index= ["COUNTY"+suffixes[0]],
                                    aggfunc = "mean").reset_index()
    county_sum1["RATING CYCLE CODE"] = suffixes[0][1:]
    county_sum1.rename(columns = dict(zip([x+suffixes[0] for x in item_list] +["COUNTY"+suffixes[0]], item_list+["COUNTY"])), inplace = True)
    county_sum2 = data1.pivot_table(values = [x+suffixes[1] for x in item_list], index= ["COUNTY"+suffixes[1]],aggfunc = "mean").reset_index()
    county_sum2["RATING CYCLE CODE"] = suffixes[1][1:]
    county_sum2.rename(columns = dict(zip([x+suffixes[1] for x in item_list] +["COUNTY"+suffixes[1]], item_list+["COUNTY"])), inplace = True)
    county_sum = pd.concat([county_sum1, county_sum2]).reset_index(drop=True)

    # Additional grouping by ride traffic level for IRI only
    if "IRI" in perf_indx:
        county_sum10 = data1.pivot_table(values = "SECTION LENGTH"+suffixes[0], 
                                        index= ["COUNTY"+suffixes[0],"RIDE SCORE TRAFFIC LEVEL"+suffixes[0]],
                                        aggfunc = "sum").reset_index()
        county_sum10["RATING CYCLE CODE"] = suffixes[0][1:]
        county_sum10.rename(columns = dict(zip(["SECTION LENGTH"+suffixes[0], "COUNTY"+suffixes[0], "RIDE SCORE TRAFFIC LEVEL"+suffixes[0]], 
                                            ["SECTION LENGTH","COUNTY", "RIDE SCORE TRAFFIC LEVEL"])),
                            inplace = True)
        county_sum10 = county_sum10.pivot(index=['COUNTY', "RATING CYCLE CODE"], 
                                        columns='RIDE SCORE TRAFFIC LEVEL',
                                        values="SECTION LENGTH").reset_index()
        

        county_sum20 = data1.pivot_table(values = "SECTION LENGTH"+suffixes[1], 
                                        index= ["COUNTY"+suffixes[1],"RIDE SCORE TRAFFIC LEVEL"+suffixes[1]],
                                        aggfunc = "sum").reset_index()
        county_sum20["RATING CYCLE CODE"] = suffixes[1][1:]
        county_sum20.rename(columns = dict(zip(["SECTION LENGTH"+suffixes[1], "COUNTY"+suffixes[1], "RIDE SCORE TRAFFIC LEVEL"+suffixes[1]], 
                                            ["SECTION LENGTH","COUNTY", "RIDE SCORE TRAFFIC LEVEL"])),
                            inplace = True)
        county_sum20 = county_sum20.pivot(index=['COUNTY', "RATING CYCLE CODE"], 
                                        columns='RIDE SCORE TRAFFIC LEVEL',
                                        values="SECTION LENGTH").reset_index()

        county_sum0 = pd.concat([county_sum10, county_sum20]).reset_index(drop=True)
        county_sum0 = county_sum0[["COUNTY", "RATING CYCLE CODE", "LOW", "MEDIUM", "HIGH"]].rename(columns = {"LOW":"LOW RIDE TRIFFIC MILES", 
                                                                                                            "MEDIUM": "MEDIUM RIDE TRIFFIC MILES",
                                                                                                            "HIGH": "HIGH RIDE TRIFFIC MILES"})
        county_sum = county_sum.merge(county_sum0, on= ["COUNTY", "RATING CYCLE CODE"],
                                      how = "left", left_index=False)
    
    count_sum = data1.groupby(by = ["COUNTY"+suffixes[0]]).size().reset_index(name = "count").rename(columns ={"COUNTY"+suffixes[0]: "COUNTY"}).sort_values(by = "COUNTY")
    county_sum = county_sum.merge(count_sum, on = "COUNTY", how = "left")
    county_sum = county_sum
    county_sum= county_sum[["COUNTY", "RATING CYCLE CODE", "count"]+
                           [x for x in county_sum.columns if x not in ["COUNTY", "RATING CYCLE CODE", "count"]]].rename(columns={"count": "Number of matching data"}).sort_values(by = ["COUNTY", "RATING CYCLE CODE"])

    # District level, true when compare year by year
    if qctype == "Year by year":
        util_list = [x for x in item_list if "UTIL" in x]
        dist_sum1 = data1.pivot_table(values = [x+suffixes[0] for x in util_list], index= ["FISCAL YEAR"+suffixes[0]],aggfunc = "mean").reset_index()
        dist_sum1.rename(columns = dict(zip([x+suffixes[0] for x in util_list] +["FISCAL YEAR"+suffixes[0]], util_list+["RATING CYCLE CODE"])), inplace= True)
        dist_sum2 = data1.pivot_table(values = [x+suffixes[1] for x in util_list], index= ["FISCAL YEAR"+suffixes[1]],aggfunc = "mean").reset_index()
        dist_sum2.rename(columns = dict(zip([x+suffixes[1] for x in util_list] +["FISCAL YEAR"+suffixes[1]], util_list+["RATING CYCLE CODE"])), inplace= True)
        dist_sum = pd.concat([dist_sum1, dist_sum2]).reset_index(drop=True)
        dist_sum = dist_sum[["RATING CYCLE CODE"]+util_list].sort_values(by = ["RATING CYCLE CODE"])
        return dist_sum, county_sum
    else:
        return county_sum

# Password checking
st.session_state["allow"] = check_password()

# Check authentication
if st.session_state["allow"]: 
    #try:     
    # Siderbar
    with st.sidebar:
        st.header("PMIS QC")

        # Loading and merging
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
            
            # Pavement type selector
            if "IRI" in perf_indx:
                pav_type = st.multiselect(label = "Pavement type", options = pav_list, default = pav_list)
            else:
                pav_type = st.multiselect(label = "Pavement type", options = ["A - ASPHALTIC CONCRETE PAVEMENT (ACP)"], default = "A - ASPHALTIC CONCRETE PAVEMENT (ACP)")
            
            # Data loading and merging
            merge_button = st.button("Load and merge data")
            if merge_button&(st.session_state.path1 is not None)&(st.session_state.path2 is not None):
                try: 
                    del st.session_state["data1"], st.session_state["data2"], st.session_state["data"], st.session_state["data_v1"], st.session_state["data_v2"]
                except:
                    pass
                st.session_state["data1"], st.session_state["data2"] = data_load(data1_path= st.session_state.path1, data2_path= st.session_state.path2, item_list = item_list)
                st.session_state["suffixes"], st.session_state["data"] = data_merge(data1 = st.session_state["data1"], data2 = st.session_state["data2"], qctype = qc_type,  item_list = item_list)
                st.session_state["data"] = pav_filter(data= st.session_state["data"], pavtype= pav_type) # Pavement type filter
            
            # Download merged data
            if "data" in st.session_state.keys():
                st.download_button("Download merged data",
                                    data = st.session_state["data"].to_csv().encode('utf-8'),
                                    file_name="merged.csv",
                                    mime="txt/csv")
        
        # Threshold filters
        st.subheader("II: Data filter")
        with st.container():
            out_type = st.selectbox("Threshold identifier", options=["percentile", "box-style"], key = 1)
            filter_items = st.multiselect(label = "Select measures to filter",
                                          options= [x for x in item_list if "UTIL" not in x], 
                                          default = [x for x in item_list if "UTIL" not in x])
            try:
                thresholds = dict()
                # for year by year
                # Based on differnce (not absolute value)
                if qc_type == "Year by year":        
                    if out_type == "percentile": # 2.5 and 97.5 percentiles
                        for item in filter_items:
                            threvals = np.nanpercentile(st.session_state["data"]["diff_"+item].values, [2.5, 97.5])
                            threshold_temp = [st.number_input(label = "diff_"+item+"_lower", value = threvals[0]), st.number_input(label = "diff_"+item+"_upper", value = threvals[1])]
                            thresholds[item] = threshold_temp

                    if out_type == "box-style": # outliers like the ones in the boxplot
                        for item in filter_items:
                            threvals = np.nanpercentile(st.session_state["data"]["diff_"+item].values, [25, 75])
                            threvals = [threvals[0]-1.5*(threvals[1]-threvals[0]), threvals[1]+1.5*(threvals[1]-threvals[0])]
                            threshold_temp = [st.number_input(label = "diff_"+item+"_lower", value = threvals[0]), st.number_input(label = "diff_"+item+"_upper", value = threvals[1])]
                            thresholds[item] = threshold_temp
                # for auditing
                # based on absolute value
                if qc_type =="Audit":
                    if out_type == "percentile":# 2.5 and 97.5 percentiles
                        for item in item_list:
                            if "UTIL" not in item:
                                threshold_temp = st.number_input(label = "diff_"+item, value = np.nanpercentile(abs(st.session_state["data"]["diff_"+item].values), 95))
                                thresholds[item] = [0, threshold_temp]

                    if out_type == "box-style": # outliers like the ones in the boxplot
                        for item in item_list:
                            if "UTIL" not in item:
                                threvals = np.nanpercentile(abs(st.session_state["data"]["diff_"+item].values), [25, 75])
                                threvals = [threvals[0]-1.5*(threvals[1]-threvals[0]), threvals[1]+1.5*(threvals[1]-threvals[0])]
                                threshold_temp = st.number_input(label = "diff_"+item, value = threvals[1])
                                thresholds[item] = [0, threshold_temp]          
            except:
                pass

            # filter add function
            filter_button = st.button("Apply filter")
            if (filter_button)&("data" in st.session_state):
                    st.session_state["data_v1"]= thre_filter(data= st.session_state["data"], thresholds = thresholds, qctype= qc_type)
    # Summary
    with st.container():
        # District level, true when compare year by year
        if "data" in st.session_state:
            data_sum = diff_summary(data= st.session_state["data"], perf_indx= perf_indx, qctype = qc_type, item_list = item_list)
            if qc_type =="Audit":
                st.subheader("County summary")
                st.dataframe(data_sum)

            if qc_type == "Year by year":
                st.subheader("District summary")
                st.dataframe(data_sum[0])
                st.subheader("County summary")
                st.dataframe(data_sum[1])

    # Distribution plots
    with st.container():
        st.subheader("Distribution Plots")
        if "data" in st.session_state:
            # Plot
            for p in perf_indx:
                list_temp = [x for x in perf_indx_list[p] if "UTIL" not in x]
                rows = int(math.ceil(len(list_temp)/3))
                st.write(p + " (Pathway - Audit/previous year) " + "distribution")
                fig = make_subplots(rows= rows, cols = 3,
                                    specs=[[{"secondary_y": True}]*3]*rows)

                i = 0
                for item in list_temp:
                    if "UTIL" not in item:
                        row = i//3+1
                        col = i%3+1
                        xdata = st.session_state["data"][["diff_"+item]]

                        if p !="IRI":
                            hist = go.Histogram(x=xdata["diff_"+item], nbinsx=50, showlegend = False)
                            ecdf = px.ecdf(xdata["diff_"+item])#, x="d_"+item)
                            ecdf = go.Scatter(x=ecdf._data[0]["x"], y=ecdf._data[0]['y'], mode='lines',  yaxis='y2', showlegend = False)
                            fig.add_trace(hist, row=row, col=col, secondary_y = False)
                            fig.add_trace(ecdf, row=row, col=col, secondary_y = True)
                            #fig.update_layout(row = row, col = col, yaxis_title='Count', yaxis2=dict(title='cdf', overlaying='y', side='right'))
                            fig.update_xaxes(title_text = "diff: "+item, row = row, col = col)
                            fig.update_yaxes(title_text="count", row=row, col=col, secondary_y=False)
                            fig.update_yaxes(title_text='cdf', row=row, col=col, secondary_y=True)
                        if p == "IRI":
                            iri_diff_bin = {"bins":[-np.inf, -200, -175, -150, -125, -100, -75, -50, -25, 0, 25, 50, 75, 100, 125, 150, 175, 200, np.inf], 
                                            "labels":["<-200", "-200-175", "-175-150", "-150-125", "-125-100", "-100-75", "-75-50", "-50-25", "-25-0", "0-25", "25-50", "50-75", "75-100", "100-125", "125-150", "150-175", "175-200", ">200"]}
                            xdata["diff_"+item] = pd.cut(xdata["diff_"+item], bins= iri_diff_bin["bins"], labels = iri_diff_bin["labels"])
                            xdata = xdata.groupby(by="diff_"+item).size().reset_index(name="count")
                            hist = go.Bar(x = xdata["diff_"+item], y = xdata["count"], showlegend = False)
                            fig.add_trace(hist, row=row, col=col)
                            fig.update_xaxes(title_text = "diff: "+item, row = row, col = col)
                        i+=1
                fig.update_layout(template="simple_white")
                fig.update_layout(height=400*rows)
                st.plotly_chart(fig, use_container_width= True)

    # Filtered data
    with st.container():
        st.subheader("Filtered data")
        if ("data_v1" in st.session_state)&("data" in st.session_state):
            try:
                st.write("Based on the selected filter, "+ str(st.session_state["data_v1"].shape[0])+" sections were obtained from "+str(st.session_state["data"].shape[0]) + " sections of the matched data")
                heading_cols = ([x+st.session_state["suffixes"][0] for x in ['FISCAL YEAR', 'SIGNED HWY AND ROADBED ID', 'BEGINNING DFO', 'ENDING DFO', 'RESPONSIBLE DISTRICT', 'COUNTY']] + 
                                [x+st.session_state["suffixes"][1] for x in ['FISCAL YEAR', 'SIGNED HWY AND ROADBED ID', 'BEGINNING DFO', 'ENDING DFO', 'RESPONSIBLE DISTRICT', 'COUNTY']]+
                                ["diff_"+x for x in item_list]+
                                [x+st.session_state["suffixes"][0] for x in item_list]+
                                [x+st.session_state["suffixes"][1] for x in item_list])
                st.dataframe(st.session_state["data_v1"][heading_cols +[x for x in st.session_state["data_v1"].columns if x not in heading_cols]],use_container_width=True)
            except:
                pass
    # Container for show distribution of outliers across different variables and location
    with st.container():
        st.subheader("Distribution of outliers")

        col1, col2 = st.columns(2, gap = "medium")
        with col1:
            if "data" in st.session_state.keys():
                st.session_state["data_v2"] = st.session_state["data"].copy()

            # County
            try: 
                st.markdown("- COUNTY")
                df1 = st.session_state["data_v1"].groupby(by = "COUNTY"+st.session_state["suffixes"][0]).agg(count_out = ("COUNTY"+st.session_state["suffixes"][0], "count"),
                                                                                                             miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                
                df2 = st.session_state["data_v2"].groupby(by = "COUNTY"+st.session_state["suffixes"][0]).agg(count_all = ("COUNTY"+st.session_state["suffixes"][0], "count"),
                                                                                                             miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                df = df1.merge(df2, how = "left", on = "COUNTY"+st.session_state["suffixes"][0]).rename(columns = {"COUNTY"+st.session_state["suffixes"][0]: "COUNTY"}).sort_values(by = "count_out", ascending = False)
                df["Percentage of all"] = 100*df["count_out"]/df["count_all"]

                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x =df["COUNTY"], y = df["count_out"], name = "Number of outliers", 
                                     customdata = df["miles_out"],
                                     hovertemplate ='<b>COUNTY</b>: %{x}'+'<br><b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}', offsetgroup=1), 
                             secondary_y= False)                          
                
                fig.add_trace(go.Bar(x =df["COUNTY"], y = df["Percentage of all"], name = "Percentage of all", 
                                     customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                     hovertemplate ='<b>COUNTY</b>: %{x}'+'<br><b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}', offsetgroup=2),
                             secondary_y= True)
                
                fig.update_xaxes(title_text="COUNTY")
                fig.update_yaxes(title_text="Number of outliers", secondary_y=False)
                fig.update_yaxes(title_text="Percentage of all", range = [0, 100], secondary_y=True)
                fig.update_layout(hoverlabel_align = 'left')
                st.plotly_chart(fig, use_container_width= True)
            except:
                pass

            # count of the filtered data based on SIGNED HWY AND ROADBED ID
            try:
                st.markdown("- SIGNED HWY AND ROADBED ID")
                df1 = st.session_state["data_v1"].groupby(by = "SIGNED HWY AND ROADBED ID"+st.session_state["suffixes"][0]).size().reset_index(name = "count_out").sort_values(by = "count_out", ascending = False)
                df1 = st.session_state["data_v1"].groupby(by = "SIGNED HWY AND ROADBED ID"+st.session_state["suffixes"][0]).agg(count_out = ("SIGNED HWY AND ROADBED ID"+st.session_state["suffixes"][0], "count"),
                                                                                                                                miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()


                df2 = st.session_state["data_v2"].groupby(by = "SIGNED HWY AND ROADBED ID"+st.session_state["suffixes"][0]).agg(count_all = ("SIGNED HWY AND ROADBED ID"+st.session_state["suffixes"][0], "count"),
                                                                                                                                miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()

                df = df1.merge(df2, how = "left", on = "SIGNED HWY AND ROADBED ID"+st.session_state["suffixes"][0]).rename(columns = {"SIGNED HWY AND ROADBED ID"+st.session_state["suffixes"][0]: "SIGNED HWY AND ROADBED ID"})
                df["Percentage of all"] = 100*df["count_out"]/df["count_all"]
                df["SIGNED HWY AND ROADBED ID"] = df["SIGNED HWY AND ROADBED ID"]

                fig = make_subplots(rows = 2, cols = 1, shared_xaxes= True)
                fig.add_trace(go.Bar(x =df["SIGNED HWY AND ROADBED ID"], y = df["count_out"], name = "Number of outliers",
                                     customdata = df["miles_out"],
                                     hovertemplate ='<b>HIGHWAY ID</b>: %{x}<br>'+'<b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}'), 
                              row=1, col=1)
                
                fig.add_trace(go.Bar(x =df["SIGNED HWY AND ROADBED ID"], y = df["Percentage of all"], name = "Percentage of all", 
                                     customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                     hovertemplate ='<b>HIGHWAY ID</b>: %{x}'+'<br><b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}'), 
                              row=2, col=1)
                
                fig.update_xaxes(title_text="SIGNED HWY AND ROADBED ID", row=2, col =1)
                fig.update_yaxes(title_text="Number of outliers", row =1, col =1)
                fig.update_yaxes(title_text="Percentage of all", range = [0, 100], row = 2, col=1)
                fig.update_layout(hoverlabel_align = 'left')
                st.plotly_chart(fig, use_container_width= True)
            except:
                pass

            # Lane number
            try:
                st.markdown("- LANE NUMBER")
                st.session_state["data_v1"]["indicator"] = st.session_state["data_v1"]["LANE NUMBER" + st.session_state["suffixes"][0]].astype("str")+"-"+st.session_state["data_v1"]["LANE NUMBER" + st.session_state["suffixes"][1]].astype("str")
                st.session_state["data_v2"]["indicator"]= st.session_state["data_v2"]["LANE NUMBER" + st.session_state["suffixes"][0]].astype("str")+"-"+st.session_state["data_v2"]["LANE NUMBER" + st.session_state["suffixes"][1]].astype("str")
                
                df1 = st.session_state["data_v1"].groupby(by = "indicator").agg(count_out = ("indicator", "count"),
                                                                                miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                
                df2 = st.session_state["data_v2"].groupby(by = "indicator").agg(count_all = ("indicator", "count"),
                                                                                miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                df = df1.merge(df2, how = "left", on = "indicator")
                df["Percentage of all"] = 100*df["count_out"]/df["count_all"]
                df.sort_values(by = "count_out", ascending = False, inplace = True)
                
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x =df["indicator"], y = df["count_out"], name = "Number of outliers", 
                                     customdata = df["miles_out"],
                                     hovertemplate ='<b>Lane</b>: %{x}<br>'+'<b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}',
                                     offsetgroup=1), 
                             secondary_y= False)
                
                fig.add_trace(go.Bar(x =df["indicator"], y = df["Percentage of all"], name = "Percentage of all", 
                                     customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                     hovertemplate ='<b>Lane</b>: %{x}'+'<br><b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}', 
                                     offsetgroup=2), 
                              secondary_y= True)
                fig.update_xaxes(title_text="LANE NUMBER")
                fig.update_yaxes(title_text="Number of outliers", secondary_y=False)
                fig.update_yaxes(title_text="Percentage of all", range = [0, 100], secondary_y=True)
                fig.update_layout(hoverlabel_align = 'left')
                st.plotly_chart(fig, use_container_width= True)
            except:
                pass
                        
            # Direction                
            try:
                st.markdown("- DIRECTION")
                st.session_state["data_v1"]["indicator"] = st.session_state["data_v1"]["DIRECTION" + st.session_state["suffixes"][0]].astype("str")+"-"+st.session_state["data_v1"]["DIRECTION" + st.session_state["suffixes"][1]].astype("str")
                st.session_state["data_v2"]["indicator"]= st.session_state["data_v2"]["DIRECTION" + st.session_state["suffixes"][0]].astype("str")+"-"+st.session_state["data_v2"]["DIRECTION" + st.session_state["suffixes"][1]].astype("str")
                df1 = st.session_state["data_v1"].groupby(by = "indicator").agg(count_out = ("indicator", "count"),
                                                                                miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                df2 = st.session_state["data_v2"].groupby(by = "indicator").agg(count_all = ("indicator", "count"),
                                                                                miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                df = df1.merge(df2, how = "left", on = "indicator")
                df["Percentage of all"] = 100*df["count_out"]/df["count_all"]
                df.sort_values(by = "count_out", ascending = False, inplace = True)

                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x =df["indicator"], y = df["count_out"], name = "Number of outliers", 
                                     customdata = df["miles_out"],
                                     hovertemplate ='<b>Direction</b>: %{x}<br>'+'<b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}', 
                                     offsetgroup=1),
                             secondary_y= False)
                
                fig.add_trace(go.Bar(x =df["indicator"], y = df["Percentage of all"], name = "Percentage of all", 
                                     customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                     hovertemplate ='<b>Direction</b>: %{x}'+'<br><b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}', 
                                     offsetgroup=2),
                              secondary_y= True)
                fig.update_xaxes(title_text="DIRECTION")
                fig.update_yaxes(title_text="Number of outliers", secondary_y=False)
                fig.update_yaxes(title_text="Percentage of all", range = [0, 100], secondary_y=True)
                fig.update_layout(hoverlabel_align = 'left')
                st.plotly_chart(fig, use_container_width= True)
            except:
                pass

            # Vehicle id           
            try:
                st.markdown("- VEHICLE ID")   
                st.session_state["data_v1"]["indicator"] = st.session_state["data_v1"]["VEHICLE ID" + st.session_state["suffixes"][0]].astype("str")+"-"+st.session_state["data_v1"]["VEHICLE ID" + st.session_state["suffixes"][1]].astype("str")
                st.session_state["data_v2"]["indicator"]= st.session_state["data_v2"]["VEHICLE ID" + st.session_state["suffixes"][0]].astype("str")+"-"+st.session_state["data_v2"]["VEHICLE ID" + st.session_state["suffixes"][1]].astype("str")
                
                df1 = st.session_state["data_v1"].groupby(by = "indicator").agg(count_out = ("indicator", "count"),
                                                                                miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                df2 = st.session_state["data_v2"].groupby(by = "indicator").agg(count_all = ("indicator", "count"),
                                                                                miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                
                df = df1.merge(df2, how = "left", on = "indicator")
                df["Percentage of all"] = 100*df["count_out"]/df["count_all"]
                df.sort_values(by = "count_out", ascending = False, inplace = True)

                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x =df["indicator"], y = df["count_out"], name = "Number of outliers",
                                     customdata = df["miles_out"],
                                     hovertemplate ='<b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}',
                                     offsetgroup=1),
                              secondary_y= False)
                fig.add_trace(go.Bar(x =df["indicator"], y = df["Percentage of all"], name = "Percentage of all", 
                                     customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                     hovertemplate ='<b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}', 
                                     offsetgroup=2), 
                              secondary_y= True)
                fig.update_xaxes(title_text="VEHICLE ID")
                fig.update_yaxes(title_text="Number of outliers", secondary_y=False)
                fig.update_yaxes(title_text="Percentage of all", range = [0, 100], secondary_y=True)
                fig.update_layout(hoverlabel_align = 'left')
                st.plotly_chart(fig, use_container_width= True)
            except:
                pass

            # Average speed
            try:
                st.markdown("- AVERAGE SPEED")

                speed_avg_bins = {"bins":[0, 10, 20, 30, 40, 50, 60, 70, 80, 90], "labels":["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70", "70-80", "80-90"]}
                speed_diff_bins = {"bins":[-np.inf, -40, -30, -20, -10, 0, 10, 20, 30, 40, np.inf], "labels":["<-40", "-40-30", "-30-20", "-20-10", "-10-0", "0-10", "10-20", "20-30", "30-40", ">40"]}

                st.session_state["data_v1"]["avg speed bins"] = pd.cut(st.session_state["data_v1"]["AVERAGE SPEED"+st.session_state["suffixes"][0]], bins = speed_avg_bins["bins"], labels = speed_avg_bins["labels"])
                st.session_state["data_v1"]["diff speed bins"] = pd.cut(st.session_state["data_v1"]["AVERAGE SPEED"+st.session_state["suffixes"][0]] - st.session_state["data_v1"]["AVERAGE SPEED"+st.session_state["suffixes"][1]], bins = speed_diff_bins["bins"], labels = speed_diff_bins["labels"])

                st.session_state["data_v2"]["avg speed bins"] = pd.cut(st.session_state["data_v2"]["AVERAGE SPEED"+st.session_state["suffixes"][0]], bins = speed_avg_bins["bins"], labels = speed_avg_bins["labels"])
                st.session_state["data_v2"]["diff speed bins"] = pd.cut(st.session_state["data_v2"]["AVERAGE SPEED"+st.session_state["suffixes"][0]] - st.session_state["data_v2"]["AVERAGE SPEED"+st.session_state["suffixes"][1]], bins = speed_diff_bins["bins"], labels = speed_diff_bins["labels"])

                df1 = st.session_state["data_v1"].groupby(by = "avg speed bins").agg(count_out = ("avg speed bins", "count"),
                                                                                     miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                df2 = st.session_state["data_v2"].groupby(by = "avg speed bins").agg(count_all = ("avg speed bins", "count"),
                                                                                     miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                df = df1.merge(df2, how = "left", on = "avg speed bins")
                df["Percentage of all"] = df["count_out"]/df["count_all"]*100

                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x =df["avg speed bins"], y = df["count_out"], name = "Number of outliers", 
                                     customdata = df["miles_out"],
                                     hovertemplate ='<b>Speed</b>: %{x}<br>'+'<b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}', 
                                     offsetgroup=1), 
                              secondary_y= False)
                fig.add_trace(go.Bar(x =df["avg speed bins"], y = df["Percentage of all"], name = "Percentage of all", 
                                     customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                     hovertemplate ='<b>Speed</b>: %{x}'+'<br><b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}', 
                                     offsetgroup=2), 
                              secondary_y= True)
                fig.update_xaxes(title_text="AVERAGE SPEED")
                fig.update_yaxes(title_text="Number of outliers", secondary_y=False)
                fig.update_yaxes(title_text="Percentage of all", range = [0, 100], secondary_y=True)
                fig.update_layout(hoverlabel_align = 'left')

                st.plotly_chart(fig, use_container_width= True)

                df1 = st.session_state["data_v1"].groupby(by = "diff speed bins").agg(count_out = ("diff speed bins", "count"),
                                                                                      miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                df2 = st.session_state["data_v2"].groupby(by = "diff speed bins").agg(count_all = ("diff speed bins", "count"),
                                                                                      miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()

                df = df1.merge(df2, how = "left", on = "diff speed bins")
                df["Percentage of all"] = df["count_out"]/df["count_all"]*100
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x =df["diff speed bins"], y = df["count_out"], name = "Number of outliers", 
                                     customdata = df["miles_out"],
                                     hovertemplate ='<b>Speed DIFF</b>: %{x}<br>'+'<b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}', 
                                     offsetgroup=1), 
                              secondary_y= False)
                fig.add_trace(go.Bar(x =df["diff speed bins"], y = df["Percentage of all"], name = "Percentage of all", 
                                     customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                     hovertemplate ='<b>Speed DIFF</b>: %{x}'+'<br><b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}', 
                                     offsetgroup=2), 
                              secondary_y= True)
                fig.update_xaxes(title_text="AVERAGE SPEED DIFF")
                fig.update_yaxes(title_text="Number of outliers", secondary_y=False)
                fig.update_yaxes(title_text="Percentage of all", range = [0, 100], secondary_y=True)
                fig.update_layout(hoverlabel_align = 'left')
                st.plotly_chart(fig, use_container_width= True)
            except:
                pass

        with col2:
                # Start time
                try: 
                    st.markdown("- START TIME")
                    df1 = st.session_state["data_v1"].groupby(by = "START TIME"+st.session_state["suffixes"][0]).agg(count_out = ("START TIME"+st.session_state["suffixes"][0], "count"),
                                                                                                                     miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                    df2 = st.session_state["data_v2"].groupby(by = "START TIME"+st.session_state["suffixes"][0]).agg(count_all = ("START TIME"+st.session_state["suffixes"][0], "count"),
                                                                                                                     miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()

                    df = df1.merge(df2, how = "left", on = "START TIME"+st.session_state["suffixes"][0]).rename(columns = {"START TIME"+st.session_state["suffixes"][0]: "START TIME"})
                    df["Percentage of all"] = 100*df["count_out"]/df["count_all"]
                    df.sort_values(by = "count_out", ascending = False, inplace = True)

                    fig = make_subplots(rows = 2, cols = 1, shared_xaxes= True)
                    fig.add_trace(go.Bar(x =df["START TIME"], y = df["count_out"], name = "Number of outliers", 
                                         customdata = df["miles_out"],
                                         hovertemplate ='<b>Time</b>: %{x}<br>'+'<b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}', 
                                         offsetgroup=1), 
                                  row = 1, col=1)
                    fig.add_trace(go.Bar(x =df["START TIME"], y = df["Percentage of all"], name = "Percentage of all", 
                                         customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                         hovertemplate ='<b>Time</b>: %{x}'+'<br><b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}', 
                                         offsetgroup=2), 
                                  row =2, col=1)
                    fig.update_xaxes(title_text="START TIME", row=2, col=1)
                    fig.update_yaxes(title_text="Number of outliers", row =1, col =1)
                    fig.update_yaxes(title_text="Percentage of all", range = [0, 100], row = 2, col=1)
                    fig.update_layout(hoverlabel_align = 'left')
                    st.plotly_chart(fig, use_container_width= True)

                    st.session_state["data_v1"]["time_diff"] = st.session_state["data_v1"]["START TIME"+st.session_state["suffixes"][0]]-st.session_state["data_v1"]["START TIME"+st.session_state["suffixes"][1]]
                    st.session_state["data_v2"]["time_diff"] = st.session_state["data_v2"]["START TIME"+st.session_state["suffixes"][0]]-st.session_state["data_v2"]["START TIME"+st.session_state["suffixes"][1]]

                    df1 = st.session_state["data_v1"].groupby(by = "time_diff").agg(count_out = ("time_diff", "count"),
                                                                                    miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                    df2 = st.session_state["data_v2"].groupby(by = "time_diff").agg(count_all = ("time_diff", "count"),
                                                                                    miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                    df = df1.merge(df2, how = "left", on = "time_diff")
                    df["time_diff"] = df["time_diff"].dt.days
                    df["Percentage of all"] = 100*df["count_out"]/df["count_all"]
                    df.sort_values(by = "count_out", ascending = False, inplace = True)

                    fig = make_subplots(rows = 2, cols = 1, shared_xaxes= True)
                    fig.add_trace(go.Bar(x =df["time_diff"], y = df["count_out"], name = "Number of outliers", 
                                         customdata = df["miles_out"],
                                         hovertemplate ='<b>Time Gap</b>: %{x}<br>'+'<b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}',
                                         offsetgroup=1), 
                                  row = 1, col=1)
                    fig.add_trace(go.Bar(x =df["time_diff"], y = df["Percentage of all"], name = "Percentage of all", 
                                         customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                         hovertemplate ='<b>Time Gap</b>: %{x}'+'<br><b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}', 
                                         offsetgroup=2), 
                                  row =2, col=1)
                    fig.update_xaxes(title_text="time_diff", row=2, col =1)
                    fig.update_yaxes(title_text="Number of outliers", row =1, col =1)
                    fig.update_yaxes(title_text="Percentage of all", range = [0, 100], row = 2, col=1)
                    fig.update_layout(hoverlabel_align = 'left')
                    st.plotly_chart(fig, use_container_width= True)
                except:
                    pass

                try:
                    # RIDE COMMENT CODE
                    st.markdown("- RIDE COMMENT CODE")
                    st.session_state["data_v1"]["indicator"] = st.session_state["data_v1"]["RIDE COMMENT CODE" + st.session_state["suffixes"][0]].astype("str")+"-"+st.session_state["data_v1"]["RIDE COMMENT CODE" + st.session_state["suffixes"][1]].astype("str")
                    st.session_state["data_v2"]["indicator"]= st.session_state["data_v2"]["RIDE COMMENT CODE" + st.session_state["suffixes"][0]].astype("str")+"-"+st.session_state["data_v2"]["RIDE COMMENT CODE" + st.session_state["suffixes"][1]].astype("str")
                    
                    df1 = st.session_state["data_v1"].groupby(by = "indicator").agg(count_out = ("indicator", "count"),
                                                                                    miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                    df2 = st.session_state["data_v2"].groupby(by = "indicator").agg(count_all = ("indicator", "count"),
                                                                                    miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                    df = df1.merge(df2, how = "left", on = "indicator")
                    df["Percentage of all"] = 100*df["count_out"]/df["count_all"]
                    df.sort_values(by = "count_out", ascending = False, inplace = True)

                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    fig.add_trace(go.Bar(x =df["indicator"], y = df["count_out"], name = "Number of outliers", 
                                         customdata = df["miles_out"],
                                         hovertemplate ='<b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}',
                                         offsetgroup=1), 
                                  secondary_y= False)
                    fig.add_trace(go.Bar(x =df["indicator"], y = df["Percentage of all"], name = "Percentage of all", 
                                         customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                         hovertemplate ='<b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}',
                                         offsetgroup=2), 
                                  secondary_y= True)
                    fig.update_xaxes(title_text="RIDE COMMENT CODE")
                    fig.update_yaxes(title_text="Number of outliers", secondary_y=False)
                    fig.update_yaxes(title_text="Percentage of all", range = [0, 100], secondary_y=True)
                    fig.update_layout(hoverlabel_align = 'left')
                    st.plotly_chart(fig, use_container_width= True)
                except:
                    pass

                # ACP RUT AUTO COMMENT CODE
                try:
                    if "RUT" in perf_indx:
                        st.markdown("- ACP RUT AUTO COMMENT CODE")
                        st.session_state["data_v1"]["indicator"] = st.session_state["data_v1"]["ACP RUT AUTO COMMENT CODE" + st.session_state["suffixes"][0]].astype("str")+"-"+st.session_state["data_v1"]["ACP RUT AUTO COMMENT CODE" + st.session_state["suffixes"][1]].astype("str")
                        st.session_state["data_v2"]["indicator"]= st.session_state["data_v2"]["ACP RUT AUTO COMMENT CODE" + st.session_state["suffixes"][0]].astype("str")+"-"+st.session_state["data_v2"]["ACP RUT AUTO COMMENT CODE" + st.session_state["suffixes"][1]].astype("str")
                        df1 = st.session_state["data_v1"].groupby(by = "indicator").agg(count_out = ("indicator", "count"),
                                                                                        miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                        df2 = st.session_state["data_v2"].groupby(by = "indicator").agg(count_all = ("indicator", "count"),
                                                                                        miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                        df = df1.merge(df2, how = "left", on = "indicator")
                        df["Percentage of all"] = 100*df["count_out"]/df["count_all"]
                        df.sort_values(by = "count_out", ascending = False, inplace = True)

                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        fig.add_trace(go.Bar(x =df["indicator"], y = df["count_out"], name = "Number of outliers", 
                                             customdata = df["miles_out"],
                                             hovertemplate ='<b>RUT COMMENT</b>: %{x}'+'<b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}',
                                             offsetgroup=1), 
                                      secondary_y= False)
                        fig.add_trace(go.Bar(x =df["indicator"], y = df["Percentage of all"], name = "Percentage of all", 
                                             customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                             hovertemplate ='<b>RUT COMMENT</b>: %{x}'+'<b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}',
                                             offsetgroup=2), 
                                      secondary_y= True)
                        fig.update_xaxes(title_text="ACP RUT AUTO COMMENT CODE")
                        fig.update_yaxes(title_text="Number of outliers", secondary_y=False)
                        fig.update_yaxes(title_text="Percentage of all", range = [0, 100], secondary_y=True)
                        fig.update_layout(hoverlabel_align = 'left')
                        st.plotly_chart(fig, use_container_width= True)
                except:
                    pass
                
                # INTERFACE FLAG                
                try:
                    # INTERFACE FLAG
                    st.markdown("- INTERFACE FLAG")
                    st.session_state["data_v1"]["indicator"] = st.session_state["data_v1"]["INTERFACE FLAG" + st.session_state["suffixes"][0]].astype("str")+"-"+st.session_state["data_v1"]["INTERFACE FLAG" + st.session_state["suffixes"][1]].astype("str")
                    st.session_state["data_v2"]["indicator"]= st.session_state["data_v2"]["INTERFACE FLAG" + st.session_state["suffixes"][0]].astype("str")+"-"+st.session_state["data_v2"]["INTERFACE FLAG" + st.session_state["suffixes"][1]].astype("str")
                    df1 = st.session_state["data_v1"].groupby(by = "indicator").agg(count_out = ("indicator", "count"),
                                                                                    miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                    df2 = st.session_state["data_v2"].groupby(by = "indicator").agg(count_all = ("indicator", "count"),
                                                                                    miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                    df = df1.merge(df2, how = "left", on = "indicator")
                    df["Percentage of all"] = 100*df["count_out"]/df["count_all"]
                    df.sort_values(by = "count_out", ascending = False, inplace = True)

                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    fig.add_trace(go.Bar(x =df["indicator"], y = df["count_out"], name = "Number of outliers", 
                                         customdata = df["miles_out"],
                                         hovertemplate ='<b>Interface</b>: %{x}<br>'+'<b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}',
                                         offsetgroup=1), 
                                  secondary_y= False)
                    fig.add_trace(go.Bar(x =df["indicator"], y = df["Percentage of all"], name = "Percentage of all", 
                                         customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                         hovertemplate ='<b>Interface</b>: %{x}'+'<br><b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}', 
                                         offsetgroup=2), 
                                  secondary_y= True)
                    fig.update_xaxes(title_text="INTERFACE FLAG")
                    fig.update_yaxes(title_text="Number of outliers", secondary_y=False)
                    fig.update_yaxes(title_text="Percentage of all", range = [0, 100], secondary_y=True)
                    fig.update_layout(hoverlabel_align = 'left')
                    st.plotly_chart(fig, use_container_width= True)
                except:
                    pass

                # LANE WIDTH
                try:
                    st.markdown("- LANE WIDTH")
                    df1 = st.session_state["data_v1"].groupby(by = "LANE WIDTH"+st.session_state["suffixes"][0]).agg(count_out = ("LANE WIDTH"+st.session_state["suffixes"][0], "count"),
                                                                                                                    miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                    df2 = st.session_state["data_v2"].groupby(by = "LANE WIDTH"+st.session_state["suffixes"][0]).agg(count_all = ("LANE WIDTH"+st.session_state["suffixes"][0], "count"),
                                                                                                                    miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()

                    df = df1.merge(df2, how = "left", on = "LANE WIDTH"+st.session_state["suffixes"][0]).rename(columns = {"LANE WIDTH"+st.session_state["suffixes"][0]: "LANE WIDTH"})
                    df["Percentage of all"] = 100*df["count_out"]/df["count_all"]
                    df.sort_values(by = "count_out", ascending = False, inplace = True)

                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    fig.add_trace(go.Bar(x =df["LANE WIDTH"], y = df["count_out"], name = "Number of outliers", 
                                         customdata = df["miles_out"],
                                         hovertemplate ='<b>LANE WIDTH</b>: %{x}<br>'+'<b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}',
                                         offsetgroup=1), 
                                  secondary_y= False)
                    fig.add_trace(go.Bar(x =df["LANE WIDTH"], y = df["Percentage of all"], name = "Percentage of all", 
                                         customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                         hovertemplate ='<b>LANE WIDTH</b>: %{x}'+'<br><b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}', 
                                         offsetgroup=2), 
                                  secondary_y= True)
                    fig.update_xaxes(title_text="LANE WIDTH")
                    fig.update_yaxes(title_text="Number of outliers", secondary_y=False)
                    fig.update_yaxes(title_text="Percentage of all", range = [0, 100], secondary_y=True)
                    fig.update_layout(hoverlabel_align = 'left')
                    st.plotly_chart(fig, use_container_width= True)
                except:
                    pass
                
                # RIDE TRAFFIC CAT
                try:
                    if "IRI" in perf_indx:
                        st.markdown("- RIDE SCORE TRAFFIC LEVEL")
                        df1 = st.session_state["data_v1"].groupby(by = "RIDE SCORE TRAFFIC LEVEL"+st.session_state["suffixes"][0]).agg(count_out = ("RIDE SCORE TRAFFIC LEVEL"+st.session_state["suffixes"][0], "count"),
                                                                                                                                        miles_out = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                        df2 = st.session_state["data_v2"].groupby(by = "RIDE SCORE TRAFFIC LEVEL"+st.session_state["suffixes"][0]).agg(count_all = ("RIDE SCORE TRAFFIC LEVEL"+st.session_state["suffixes"][0], "count"),
                                                                                                                                        miles_all = ("SECTION LENGTH"+st.session_state["suffixes"][0], "sum")).reset_index()
                        df2["data"] = "all matched"
                        df = df1.merge(df2, how = "left", on = "RIDE SCORE TRAFFIC LEVEL"+st.session_state["suffixes"][0]).rename(columns = {"RIDE SCORE TRAFFIC LEVEL"+st.session_state["suffixes"][0]: "RIDE SCORE TRAFFIC LEVEL"})
                        df["Percentage of all"] = 100*df["count_out"]/df["count_all"]
                        df.sort_values(by = "count_out", ascending = False, inplace = True)

                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        fig.add_trace(go.Bar(x =df["RIDE SCORE TRAFFIC LEVEL"], y = df["count_out"], name = "Number of outliers", 
                                             customdata = df["miles_out"],
                                             hovertemplate ='<b>RIDE TRAFFIC</b>: %{x}<br>'+'<b>Outlier data</b>: %{y:.0f}<br>'+'<b>Outlier Miles</b>:%{customdata:.2f}',
                                             offsetgroup=1), 
                                      secondary_y= False)
                        fig.add_trace(go.Bar(x =df["RIDE SCORE TRAFFIC LEVEL"], y = df["Percentage of all"], name = "Percentage of all", 
                                             customdata = np.stack((df["count_all"], df["miles_all"]), axis = -1),
                                             hovertemplate ='<b>RIDE TRAFFIC</b>: %{x}'+'<br><b>Outlier PCT</b>: %{y:.1f}'+'<br><b>All data</b>:%{customdata[0]:.0f}'+'<br><b>Total Miles</b>:%{customdata[1]:.2f}',
                                             offsetgroup=2), 
                                      secondary_y= True)
                        fig.update_xaxes(title_text="RIDE SCORE TRAFFIC LEVEL")
                        fig.update_yaxes(title_text="Number of outliers", secondary_y=False)
                        fig.update_yaxes(title_text="Percentage of all", range = [0, 100], secondary_y=True)
                        fig.update_layout(hoverlabel_align = 'left')
                        st.plotly_chart(fig, use_container_width= True)
                except:
                    pass
    #except:
    #    pass
