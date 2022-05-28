########### Google Anlaytics 
# import pathlib
# from bs4 import BeautifulSoup
# import logging
# import shutil

# def inject_ga():
#     GA_ID = "google_analytics"

#     # Note: Please replace the id from G-XXXXXXXXXX to whatever your
#     # web application's id is. You will find this in your Google Analytics account
    
#     GA_JS = """
#     <!-- Global site tag (gtag.js) - Google Analytics -->
#     <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
#     <script>
#         window.dataLayer = window.dataLayer || [];
#         function gtag(){dataLayer.push(arguments);}
#         gtag('js', new Date());
#         gtag('config', 'G-XXXXXXXXXX');
#     </script>
#     """

#     # Insert the script in the head tag of the static template inside your virtual
#     index_path = pathlib.Path(st.__file__).parent / "static" / "index.html"
#     logging.info(f'editing {index_path}')
#     soup = BeautifulSoup(index_path.read_text(), features="html.parser")
#     if not soup.find(id=GA_ID):  # if cannot find tag
#         bck_index = index_path.with_suffix('.bck')
#         if bck_index.exists():
#             shutil.copy(bck_index, index_path)  # recover from backup
#         else:
#             shutil.copy(index_path, bck_index)  # keep a backup
#         html = str(soup)
#         new_html = html.replace('<head>', '<head>\n' + GA_JS)
#         index_path.write_text(new_html)
# inject_ga()

#######################################################
####################################################### display_main_page.py
import streamlit as st
import json
import folium
from streamlit_folium import folium_static
import pandas as pd
import numpy as np
import altair as alt
from altair import * 
import utils
import requests
from PIL import Image
import plotly.graph_objects as go
import pickle
import altair as alt 
import os
import datetime

hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Read the basic information from dictionary
with open('./dictionaries/master_dict.json') as json_file:
    master_dict = json.load(json_file)
    
today = datetime.datetime.now().strftime('%Y%m%d')
today_st = datetime.datetime.now().strftime('%m-%d-%Y')

# just in case there is no updated file 
def newest(path):
    files = os.listdir(path)
    paths = [os.path.join(path, basename) for basename in files]
    return max(paths, key=os.path.getctime)

date_path = "./data/"
new_path = newest(date_path)
latest_date = new_path.split('_')[-1].split('.')[0]

if latest_date != today:
    today = latest_date
    today_st = latest_date[:4] + '-' + latest_date[4:6] + '-' + latest_date[6:]
#     st.error(f"Note that the current file date: {latest_date}")

df_final = pd.read_csv(f"./data/df_forcasting_{today}.csv", sep='\t')
with open(f'./data/stock_history_{today}.pickle', 'rb') as handle:
    stock_history = pickle.load(handle) 
    
# Read CSS 
def local_css(file_name):
    with open(file_name) as f:
        st.markdown('<style>{}</style>'.format(f.read()), unsafe_allow_html=True)
        
########################################################################################
########################################################################################
sector_list = ['Basic Materials', 'Consumer Cyclical', 'Healthcare', 
               'Industrials', 'Financial Services', 'Technology', 'Energy', 
               'Consumer Defensive', 'Communication Services','Utilities', 'Real Estate']

def get_sector_period(date_start, duration_days):
    date_start = date_start.strftime('%Y-%m-%d')
    df_all = pd.DataFrame()
    for ticker in stock_history.keys():
        df_temp = stock_history[ticker]
        df_temp = df_temp[df_temp["Date"] < date_start].iloc[-duration_days:]
        df_temp.reset_index(inplace=True, drop=True)

        if len(df_temp) > duration_days-1:
            df_temp["ticker"] = ticker
            df_temp["sector"] = df_final[df_final["ticker"] == ticker]["sector"].tolist()[0]
            df_temp["diff_maxmin"] = df_temp["Close"].max() - df_temp["Close"].min()
            df_temp["diff_close"] = df_temp.iloc[-1]["Close"] - df_temp.iloc[0]["Close"] 
            df_temp["ch_per_1_mean"] = df_temp["ch_per_1"].mean()
            df_temp = df_temp[["ticker", "sector", "Date", "Close", "Volume", 
                               "diff_maxmin", "diff_close", "ch_per_1_mean"]]
            df_all = df_all.append(df_temp)

    output_dict = {}
    for sector in sector_list:
        output_dict[sector] = {}

    df_filter = df_all[df_all["diff_close"] > 0]
    for sector in sector_list:
        df_filter_temp = df_filter[df_filter["sector"] == sector]
        output_dict[sector]["pos_diff_close"] = df_filter_temp["ticker"].unique().tolist()

    df_filter = df_all[df_all["diff_close"] < 0]
    for sector in sector_list:
        df_filter_temp = df_filter[df_filter["sector"] == sector]
        output_dict[sector]["neg_diff_close"] = df_filter_temp["ticker"].unique().tolist()

    df_positive = df_all[df_all["diff_close"] > 0].groupby("sector")["ticker"].nunique().reset_index(drop=False)
    df_positive.rename(columns={"ticker": "diff_close_positive"}, inplace=True)
    df_negative = df_all[df_all["diff_close"] < 0].groupby("sector")["ticker"].nunique().reset_index(drop=False)
    df_negative.rename(columns={"ticker": "diff_close_negative"}, inplace=True)
    df_total = df_all.groupby("sector")["ticker"].nunique().reset_index(drop=False)
    df_total.rename(columns={"ticker": "total"}, inplace=True)


    df_final_analysis = pd.merge(df_total, df_positive, on="sector", how="left")
    df_final_analysis = pd.merge(df_final_analysis, df_negative, on="sector", how="left")

    df_final_analysis['diff_close_positive'] = df_final_analysis['diff_close_positive'].replace(np.nan, 0)
    df_final_analysis['diff_close_negative'] = df_final_analysis['diff_close_negative'].replace(np.nan, 0)

    df_final_analysis["p_perc"] = round(df_final_analysis["diff_close_positive"]/df_final_analysis["total"]*100, 2)
    df_final_analysis["n_perc"] = round(df_final_analysis["diff_close_negative"]/df_final_analysis["total"]*100, 2)

    top_labels = ['Price Up', 'Price Down']
    colors = ['rgba(211,92,55, 0.8)', 'rgba(214,198,185, 0.8)']
    x_data = df_final_analysis[["p_perc", "n_perc"]].values.tolist()
    y_data = df_final_analysis["sector"].tolist()
    
    time_start = df_temp.iloc[0]["Date"].strftime('%Y-%m-%d') 
    time_last = df_temp.iloc[-1]["Date"].strftime('%Y-%m-%d') 
    
    fig = go.Figure()
    for i in range(0, len(x_data[0])):
        for xd, yd in zip(x_data, y_data):
            fig.add_trace(go.Bar(
                x=[xd[i]], y=[yd],
                orientation='h',
                marker=dict(color=colors[i],
                            line=dict(color='rgb(248, 248, 249)', width=1))
                ))

    fig.update_layout(
        title = f'Time Period: {time_start} & {time_last}',
        xaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
            domain=[0.15, 1]
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
        ),
        barmode='stack',
        paper_bgcolor='rgb(248, 248, 255)',
        plot_bgcolor='rgb(248, 248, 255)',
        margin=dict(l=120, r=10, t=140, b=80),
        showlegend=False,
    )

    annotations = []
    for yd, xd in zip(y_data, x_data):
        # labeling the y-axis
        annotations.append(dict(xref='paper', yref='y',
                                x=0.13, y=yd,
                                xanchor='right',
                                text=str(yd),
                                font=dict(family='Arial', size=14,
                                          color='rgb(68,76,92)'),
                                showarrow=False, align='right'))

        # labeling (positive)
        annotations.append(dict(xref='x', yref='y',
                                x= (xd[0] +1) / 2, y=yd,
                                text=str(xd[0]) + '%',
                                font=dict(family='Arial', size=14,
                                          color='rgb(116,71,0)'),
                                showarrow=False))
        # labeling on the left
        if yd == y_data[-1]:
            annotations.append(dict(xref='x', yref='paper',
                                    x=(xd[0]+1) / 2, y=1.1,
                                    text=top_labels[0],
                                    font=dict(family='Arial', size=14,
                                              color='rgb(68,76,92)'),
                                    showarrow=False))
        space = xd[0] + 2
        for i in range(1, len(xd)):
                # labeling negative percentage
                annotations.append(dict(xref='x', yref='y',
                                        x=space + (xd[i]/2), y=yd,
                                        text=str(xd[i]) + '%',
                                        font=dict(family='Arial', size=14,
                                                  color='rgb(191,154,119)'),
                                        showarrow=False))
                # labeling negative title
                if yd == y_data[-1]:
                    annotations.append(dict(xref='x', yref='paper',
                                            x=space + (xd[i]/2), y=1.1,
                                            text=top_labels[i],
                                            font=dict(family='Arial', size=14,
                                                      color='rgb(68,76,92)'),
                                            showarrow=False))
                space += xd[i]

    annotations.append(dict(xref='paper', yref='paper',
                            x= 0.15, y=-0.109,
                            text="""Reference: yfinance S&P 500 data                         
                            """,
                            font=dict(family='Arial', size=10, color='rgb(150,150,150)'),
                            showarrow=False))

    fig.update_layout(annotations=annotations)
    return fig
#     fig.show()
######################################################################
def get_sector_period_dict(date_start, duration_days):
    date_start = date_start.strftime('%Y-%m-%d')
    df_all = pd.DataFrame()
    for ticker in stock_history.keys():
        df_temp = stock_history[ticker]
        df_temp = df_temp[df_temp["Date"] < date_start].iloc[-duration_days:]
        df_temp.reset_index(inplace=True, drop=True)

        if len(df_temp) > duration_days-1:
            df_temp["ticker"] = ticker
            df_temp["sector"] = df_final[df_final["ticker"] == ticker]["sector"].tolist()[0]
            df_temp["diff_maxmin"] = df_temp["Close"].max() - df_temp["Close"].min()
            df_temp["diff_close"] = df_temp.iloc[-1]["Close"] - df_temp.iloc[0]["Close"] 
            df_temp["ch_per_1_mean"] = df_temp["ch_per_1"].mean()
            df_temp = df_temp[["ticker", "sector", "Date", "Close", "Volume", 
                               "diff_maxmin", "diff_close", "ch_per_1_mean"]]
            df_all = df_all.append(df_temp)

    output_dict = {}
    for sector in sector_list:
        output_dict[sector] = {}

    df_filter = df_all[df_all["diff_close"] > 0]
    for sector in sector_list:
        df_filter_temp = df_filter[df_filter["sector"] == sector]
        output_dict[sector]["pos_diff_close"] = df_filter_temp["ticker"].unique().tolist()

    df_filter = df_all[df_all["diff_close"] < 0]
    for sector in sector_list:
        df_filter_temp = df_filter[df_filter["sector"] == sector]
        output_dict[sector]["neg_diff_close"] = df_filter_temp["ticker"].unique().tolist()
        
    return output_dict

def sector_df(output_dict, sector, up): 
    indu_col = ["ticker", "close_price", "longName", "url"]
    if up == True: 
        df_temp = df_final[df_final["ticker"].isin(output_dict[sector]["pos_diff_close"])][indu_col].sort_values("close_price")
    else: 
        df_temp = df_final[df_final["ticker"].isin(output_dict[sector]["neg_diff_close"])][indu_col].sort_values("close_price")
    
    df_temp["close_price"] = df_temp["close_price"].round(1)
    df_temp["close_price"] = '$' + df_temp["close_price"].astype(str)
    df_temp.reset_index(inplace=True, drop=True)
    df_temp.rename(columns={"ticker": "Ticker", 
                       "close_price": "Close Price", 
                       "longName": "Company Name",
                       "url": "URL"}, inplace=True)
    return df_temp
    
######################################################################
######################################################################
# Download chart data points as csv
@st.cache
def convert_df(df):
    # important: cache the conversion to prevent computation on every rerun.
    return df.to_csv().encode('utf-8')

def show(result, model, task, input_dict):
    with st.container():
        result_container = st.container()
        col1, col2 = st.columns([2, 20])
        
        if result: 
            with result_container:
                with col2: 
                    st.markdown("<h2 style='text-align: center; color: red;'>Oops!! No data found. Try different inputs. </h2>", unsafe_allow_html=True)

###################################################################### HOME   
######################################################################
        elif model == "Home":
            st.markdown("<h1 style='text-align: center; color: black;'>Find the Right Ticker for You!</h1>", unsafe_allow_html=True)
            
            left_info_col, right_info_col = st.columns([1, 2])
            
            left_info_col.write('')
            main_image = Image.open(f'./images/main_stock.png')
            left_info_col.image(main_image, width=220)
            left_info_col.write('')
            
            right_info_col.markdown("""
            
            Welcome! This site is an example of an app implementation of the data analysis, forecasting, and an automated pipeline introduced in the [Class101 Data Science Practical Project lecture](https://class101.net/products/l4O941573GhUs5qxKhIc). The data analysis and forecasting models displayed here are not optimized for investment purposes. Therefore, this website is not responsible for any investment decisions.""")
            
            intro_ko = '<p style="font-family:Courier; color:gray; font-size: 13px;">안녕하세요. 이 사이트는 [클래스101 데이터 과학 실무 프로젝트] 강의에서 소개된 데이터 분석, 예측모델 및 데이터 파이프라인의 앱 구현 사례입니다. 여기에 표시된 데이터 분석 및 예측 모델은 투자 목적으로 최적화되지 않았으며, 개인 투자에 대해 책임을 지지 않습니다.</p>'
            right_info_col.markdown(intro_ko, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("""
            ### Creating monetization - Ad""")
            
            HtmlFile = open('./modules/adsense.html', 'r', encoding='utf-8')
            source_code = HtmlFile.read()
            components.html(source_code, height=600)

#             st.markdown(
#                 """
#                 <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5073055552400117"
#      crossorigin="anonymous"></script>
# <!-- streamlit_ad -->
# <ins class="adsbygoogle"
#      style="display:block"
#      data-ad-client="ca-pub-5073055552400117"
#      data-ad-slot="3052417980"
#      data-ad-format="auto"
#      data-full-width-responsive="true"></ins>
# <script>
#      (adsbygoogle = window.adsbygoogle || []).push({});
# </script>
#                 """,
#                 unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("""
            ### Usage
            In the left menu SP&P500, you can find the right ticker for you, depending on your **investment budget**, **sector of interest**, and **risk level** you can take on. Along with the corresponding ticker, the forecasted stock price calculated by the time series ARIMA model is also provided.""") 
           
            usage_ko = '<p style="font-family:Courier; color:gray; font-size: 13px;">왼쪽 메뉴 SP&P500에서, <투자 예산>, <관심 섹터>, <본인 투자 위험도>를 입력하면 SP&500 티커 중 여기에 해당되는 티커와 함께 시계열 ARIMA 모델로 계산된 예상 주가도 같이 제공합니다. 데이터 분석, 예측 모델, 클라우드 서비스 자동화 과정이 강의에 제공되어 있으므로 코드는 따로 공개하지 않습니다. </p>'
            st.markdown(usage_ko, unsafe_allow_html=True) 

            st.markdown("---")
            st.markdown("""Developed and Maintained by Jeeyoung Lee: Data Scientist & Autor """)
            st.markdown("[[클래스101] 데이터 과학 실무 프로젝트](https://class101.net/products/l4O941573GhUs5qxKhIc)")
            st.markdown("""You are always welcome to e-mail: <a href="mailto:statnmath.datascience@gmail.com>"> statnmath.datascience@gmail.com</a>""" , unsafe_allow_html=True)
            st.markdown("""Copyright (c) 2022 Jeeyoung Lee""")              
            
###################################################################### S&P500
        elif model == "S&P500":
            if len(input_dict['sector']) == 0: 
                with result_container:
                    with col2: 
                        st.markdown("<h2 style='text-align: center; color: orange;'> Please submit inputs. </h2>", unsafe_allow_html=True)
        
            else:
                # Filter the stocks 
                df_temp = df_final[df_final["sector"].isin(input_dict['sector'])]
                
                # filter by timeframe (period)
                if input_dict["period"] == "less than 3 months":
                    df_temp["cutoff_bin"] = utils.pct_rank_qcut(df_temp["cutoff_1"], 3)
                    df_temp["cutoff_skew"] = df_temp["skew_1"]
                    
                elif input_dict["period"] == "less than 6 months":                
                    df_temp["cutoff_bin"] = utils.pct_rank_qcut(df_temp["cutoff_60"], 3)
                    df_temp["cutoff_skew"] = df_temp["skew_60"]

                elif input_dict["period"] == "more than 6 months":  
                    df_temp["cutoff_bin"] = utils.pct_rank_qcut(df_temp["cutoff_120"], 3)
                    df_temp["cutoff_skew"] = df_temp["skew_120"]
                    
                df_temp = df_temp[df_temp["cutoff_bin"] == input_dict["risk"]]
                df_temp = df_temp.sort_values(by="cutoff_skew", ascending=False)
#                 df_temp = df_temp[["ticker", "close_price", "industry", "sector", "url", "cutoff_skew"]]
                df_temp.reset_index(inplace=True, drop=True)
                df_temp = df_temp.head()

                with result_container:
                    st.title(f"🎯 Result [{today_st}]")
                    df_temp_table = f"""
| **Ticker** | **Company Name** |**Sector** | **Industry** | **Close Price** | 
|-------|-------|-------|------|------|
|{df_temp.iloc[0]['ticker']}|**{df_temp.iloc[0]['longName']}**|{df_temp.iloc[0]['sector']}|{df_temp.iloc[0]['industry']}|${round(df_temp.iloc[0]['close_price'])}|   
|{df_temp.iloc[1]['ticker']}|**{df_temp.iloc[1]['longName']}** |{df_temp.iloc[1]['sector']}|{df_temp.iloc[1]['industry']}|${round(df_temp.iloc[1]['close_price'])}|      
|{df_temp.iloc[2]['ticker']}|**{df_temp.iloc[2]['longName']}** |{df_temp.iloc[2]['sector']}|{df_temp.iloc[2]['industry']}|${round(df_temp.iloc[2]['close_price'])}|      
|{df_temp.iloc[3]['ticker']}|**{df_temp.iloc[3]['longName']}** |{df_temp.iloc[3]['sector']}|{df_temp.iloc[3]['industry']}|${round(df_temp.iloc[3]['close_price'])}|      
|{df_temp.iloc[4]['ticker']}|**{df_temp.iloc[4]['longName']}** |{df_temp.iloc[4]['sector']}|{df_temp.iloc[4]['industry']}|${round(df_temp.iloc[4]['close_price'])}|      
                                     """
                    st.markdown(df_temp_table, unsafe_allow_html=True) 
                    
                    tickers = df_temp["ticker"].tail().unique().tolist()
                    
                    symbols = st.multiselect("Choose stocks to visualize", tickers, tickers[:2])
                    df_graph = pd.DataFrame()
                    for i in symbols:
                        print(i)
                        df_temp = stock_history[i].iloc[-300:][["Date", "Close"]]
                        df_temp["ticker"] = i
                        df_graph = df_graph.append(df_temp, ignore_index = True)
                
                    chart = utils.get_chart(df_graph)
                    st.altair_chart(chart, use_container_width=True)
###################################################################### Sector Report
######################################################################
        elif model == "Sector Report":
            st.markdown("<h3 style='text-align: center; color: orange;'> I. Percentage in Price Up/Down by Sectors.</h3>", unsafe_allow_html=True)               
            st.markdown("""
            The graph below shows the percentage of price increases/declines among tickets included in each sector for 20 days from the base date. You can select a **reference date** from the left calendar and **time period** The ticker lists based on close price increases/declines by sector can be found in the table below.
            """)
            sector_ko = '<p style="font-family:Courier; color:gray; font-size: 13px;">아래 그래프는 기준일로부터 20일 이전 기간 동안 각 섹터에 포함된 티켓 중 가격 상승/하락 비율을 보여줍니다. 왼쪽 달력에서 [기준 날짜] 및 [기간]을 선택할 수 있습니다. 각 섹터별 가격 상승/하락에 따른 티커는 아래 표에서 확인할 수 있습니다. </p>'
            st.markdown(sector_ko, unsafe_allow_html=True)
            
            # graph
            st.plotly_chart(get_sector_period(input_dict["start_day"], input_dict["duration"]),
                           use_container_width=True)
            
            st.markdown("<h3 style='text-align: center; color: orange;'> II. Ticker Lists by Price Up/Down in This Period.</h3>", unsafe_allow_html=True) 
            
            # get the output dicitonary 
            output_dict = get_sector_period_dict(input_dict["start_day"], input_dict["duration"])
            
            option = st.selectbox("Select the Sector", ('Utilities', 'Technology', 'Real Estate', 'Industrials', 'Healthcare', 'Financial Services', 'Energy', 'Consumer Defensive', 'Consumer Cyclical', 'Communication Services' 'Basic Materials'))
            
            # Display dataframe
            df_up = sector_df(output_dict, option, True)
            df_down = sector_df(output_dict, option, False)
            
            st.markdown("<h6 style='text-align: left; color: navy;'> (1) Close-Price UP Tickers.</h6>", unsafe_allow_html=True) 
            if len(df_up) != 0:
                st.dataframe(df_up)
            else: 
                st.markdown("There are no tickets that have gone up in close price for a given period of time.")
                
            st.markdown("<h6 style='text-align: left; color: navy;'> (2) Close-Price DOWN Tickers.</h6>", unsafe_allow_html=True)    
            if len(df_down) != 0:     
                st.dataframe(df_down)
            else:
                st.markdown("There are no tickets that have went down in close price for a given period of time.")
                
            
    
if __name__ == "__main__":
    show()
    