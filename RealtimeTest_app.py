import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import pydeck as pdk
import snowflake.connector
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.pyplot import figure
import geopandas
import altair as alt
import datetime
from PIL import Image

st.set_page_config(layout="wide")
st.title('US Traffic and Weather Events')

# Initialize connection.
# Uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    return snowflake.connector.connect(**st.secrets["snowflake"])

conn = init_connection()

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes
@st.experimental_memo
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    d = st.date_input(
        "Starting Date",
        datetime.date(2016, 8, 1))
        
with col2:
    d2 = st.date_input(
        "Ending Date",
        datetime.date(2019, 7, 6))

if(d < datetime.date(2016, 8, 1)):
    d = datetime.date(2016, 8, 1)

if(d2 > datetime.date(2020, 12, 31)):
    d2 = datetime.date(2020, 12, 31)

if(d > d2):
    d_temp = d
    d = d2
    d2 = d_temp

start = d.strftime('%m/%d/%Y')
end = d2.strftime('%m/%d/%Y')

total_events_by_day = run_query("SELECT day, sum(traffic_events) as traffic_events, sum(weather_events) as weather_events from TRIGGO_EXAMPLES_DATABASE.ANALYTICS.DAILY_EVENTS_BY_CITY where day < '"+ end +"' and day > '"+ start +"' group by day order by day ;")

days = [row[0] for row in total_events_by_day]

traffic = [row[1] for row in total_events_by_day]

weather = [row[2] for row in total_events_by_day]

if st.checkbox('Show raw data'):
    st.subheader('Raw data: Total Events by Day')
    st.write(total_events_by_day)

col1, col2, col3 = st.columns(3)

# Total Daily US Traffic Events

with col1:
    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis.set_label_text("Year")
    ax.yaxis.set_label_text("Events")

    ax.set_title('Total Daily US Traffic Events', fontstyle='italic')

    ax.plot(days, traffic)

    figure(figsize=(160, 6), dpi=160)

    st.pyplot(fig)

# Total Daily US Traffic Events

with col2:
    fig2, ax2 = plt.subplots()

    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_minor_locator(mdates.MonthLocator())
    ax2.xaxis.set_label_text("Year")
    ax2.yaxis.set_label_text("Events")

    ax2.set_title('Total Daily US Weather Events', fontstyle='italic')

    ax2.plot(days, weather)

    st.pyplot(fig2)

# Average Traffic Events by Weather Events Number

with col3:
    average_traffic_by_weather = run_query("select weather_events, avg(traffic_events) from TRIGGO_EXAMPLES_DATABASE.ANALYTICS.DAILY_EVENTS_BY_CITY where day < '01/01/2020' group by weather_events order by weather_events;")

    avg_traffic = [row[1] for row in average_traffic_by_weather]

    weather_events = [row[0] for row in average_traffic_by_weather]

    fig3, ax3 = plt.subplots()

    ax3.set_title('Average Traffic Events by Weather from Aug 2016 to Feb 2020', fontstyle='italic')

    ax3.xaxis.set_label_text("Weather Events")
    ax3.yaxis.set_label_text("Traffic Events")

    ax3.plot(weather_events, avg_traffic)

    st.pyplot(fig3)

# Frequency Distribution of Traffic and Weather Events from Aug 2016 to Dec 2020

col1, col2= st.columns(2)

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes
@st.experimental_memo
def query_dataframe(query):
    with conn.cursor() as cur:
        cur.execute(query)
        data = cur.fetchall()
        if data:
            df = pd.DataFrame(data)
        return df

df = query_dataframe("select * from TRIGGO_EXAMPLES_DATABASE.ANALYTICS.TOTAL_EVENTS_BY_STATE;")

if not df.empty:
    df = df.rename(columns={df.columns[0]: "STUSPS", df.columns[1]: "TotalTraffic", df.columns[2]: "TotalWeather"})
    #st.write(df)

states = geopandas.read_file('data/usa-states-census-2014.shp')


map_and_stats=states.merge(df, on="STUSPS")

#st.write(map_and_stats)

with col1:

    fig4, ax4 = plt.subplots(1, figsize=(10, 10))
    plt.xticks(rotation=90)

    ax4.set_title('Frequency Distribution of Traffic Events from Aug 2016 to Dec 2020', fontstyle='italic')

    map_and_stats.plot(column="TotalTraffic", cmap="Reds", linewidth=0.4, ax=ax4, edgecolor=".4")

    traffic_column = map_and_stats["TotalTraffic"]
    max_traffic = traffic_column.max()

    bar_info = plt.cm.ScalarMappable(cmap="Reds", norm=plt.Normalize(vmin=0, vmax=max_traffic))
    bar_info._A = []
    cbar = fig4.colorbar(bar_info,fraction=0.03, pad=0.04)

    ax4.xaxis.set_label_text("Longitude")
    ax4.yaxis.set_label_text("Latitude")

    st.pyplot(fig4)

with col2:

    fig5, ax5 = plt.subplots(1, figsize=(10, 10))
    plt.xticks(rotation=90)

    ax5.set_title('Frequency Distribution of Weather Events from Aug 2016 to Dec 2020', fontstyle='italic')

    map_and_stats.plot(column="TotalWeather", cmap="Blues", linewidth=0.4, ax=ax5, edgecolor=".4")

    weather_column = map_and_stats["TotalWeather"]
    max_weather = weather_column.max()

    bar_info = plt.cm.ScalarMappable(cmap="Blues", norm=plt.Normalize(vmin=0, vmax=max_weather))
    bar_info._A = []
    cbar = fig5.colorbar(bar_info,fraction=0.03, pad=0.04)

    ax5.xaxis.set_label_text("Longitude")
    ax5.yaxis.set_label_text("Latitude")

    st.pyplot(fig5)

image = Image.open('images/TrafficEvents_by_WeatherEvents.png')

st.image(image)

image2 = Image.open('images/TrafficEvents_by_WeatherSeverity.png')

st.image(image2)

image3 = Image.open('images/TrafficEvents_by_Hour.png')

st.image(image3)

image4 = Image.open('images/AvgofprobababilitiesofTraffic_EventsbyHourofDayonClearWeather.png')

st.image(image4)

image5 = Image.open('images/AvgofTrafficEventsbyHoursonBadWeather.png')

st.image(image5)

image6 = Image.open('images/AvgofTraffic_SeveritybyWeather_Severity.png')

st.image(image6)

image7 = Image.open('images/AvgofTraffic_SeveritybyHour.png')

st.image(image7)

# col1, col2, col3 = st.columns([1, 1, 3])
# with col1:
#     d = st.date_input(
#         "Starting Date",
#         datetime.date(2017, 1, 1))
        
# with col2:
#     d2 = st.date_input(
#         "Ending Date",
#         datetime.date(2017, 12, 31))

# if(d < datetime.date(2017, 1, 1)):
#     d = datetime.date(2017, 1, 1)

# if(d2 > datetime.date(2017, 12, 31)):
#     d2 = datetime.date(2017, 12, 31)

# if(d > d2):
#     d_temp = d
#     d = d2
#     d2 = d_temp

# start = d.strftime('%m/%d/%Y')
# end = d2.strftime('%m/%d/%Y')

total_events_in_texas = run_query('SELECT "Days", count(case when "Traffic_Type" != \'None\' then 1 end) as real_events, count(case when "prediction" != \'None\' then 1 end) as predicted_events from DATAIKU_DATABASE.DATAIKU_SCHEMA.SCOREDATA_TEXAS_2017_SCORED_WEATHERTRAFFICEVENTS group by "Days" order by "Days";')

days = [row[0] for row in total_events_in_texas]

traffic = [row[1] for row in total_events_in_texas]

prediction = [row[2] for row in total_events_in_texas]

col1, col2= st.columns(2)

with col1:
    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis.set_label_text("Year")
    ax.yaxis.set_label_text("Events")

    ax.set_title('Total Daily Texas Traffic Events in 2017 (real)', fontstyle='italic')

    ax.plot(days, traffic)

    figure(figsize=(160, 6), dpi=160)

    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis.set_label_text("Year")
    ax.yaxis.set_label_text("Events")

    ax.set_title('Total Daily Texas Traffic Events in 2017 (Prediction)', fontstyle='italic')

    ax.plot(days, prediction)

    figure(figsize=(160, 6), dpi=160)

    st.pyplot(fig)

col1, col2, col3= st.columns([1, 4, 1])

with col2:
    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis.set_label_text("Year")
    ax.yaxis.set_label_text("Events")

    ax.set_title('Total Daily Texas 2017 Traffic Events Comparation', fontstyle='italic')

    ax.plot(days, traffic)
    ax.plot(days, prediction)

    figure(figsize=(160, 6), dpi=160)

    st.pyplot(fig)

success_rate = run_query('SELECT count(case when "Traffic_Type" != \'None\' or "prediction" != \'None\' then 1 end) as Total, count(case when ("Traffic_Type" != \'None\' or "prediction" != \'None\') and "Traffic_Type" = "prediction" then 1 end) as RightPredictions from DATAIKU_DATABASE.DATAIKU_SCHEMA.SCOREDATA_TEXAS_2017_SCORED_WEATHERTRAFFICEVENTS;')

Total = [row[0] for row in success_rate][0]

Sucess = [row[1] for row in success_rate][0]

st.write("Sucess rate = " + str(Sucess/Total))






total_events_in_texas = run_query('SELECT DATE_TRUNC(day,"StartTime_Weather") as "Days", count(case when "Traffic_Type" != \'None\' then 1 end) as real_events, count(case when "prediction" != \'None\' then 1 end) as predicted_events from DATAIKU_DATABASE.DATAIKU_SCHEMA.TEXAS_EVENTS_2017_SCORED_WEATHERTRAFFICEVENTS group by "Days" order by "Days";')

days = [row[0] for row in total_events_in_texas]

traffic = [row[1] for row in total_events_in_texas]

prediction = [row[2] for row in total_events_in_texas]

col1, col2= st.columns(2)

with col1:
    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis.set_label_text("Year")
    ax.yaxis.set_label_text("Events")

    ax.set_title('Total Daily Texas Traffic Events During Weather Events in 2017 (real)', fontstyle='italic')

    ax.plot(days, traffic)

    figure(figsize=(160, 6), dpi=160)

    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis.set_label_text("Year")
    ax.yaxis.set_label_text("Events")

    ax.set_title('Total Daily Texas Traffic Events During Weather Events in 2017 (Prediction)', fontstyle='italic')

    ax.plot(days, prediction)

    figure(figsize=(160, 6), dpi=160)

    st.pyplot(fig)

col1, col2, col3= st.columns([1, 4, 1])

with col2:
    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis.set_label_text("Year")
    ax.yaxis.set_label_text("Events")

    ax.set_title('Total Daily Texas 2017 Traffic Events During Weather Events Comparation', fontstyle='italic')

    ax.plot(days, traffic)
    ax.plot(days, prediction)

    figure(figsize=(160, 6), dpi=160)

    st.pyplot(fig)

success_rate = run_query('SELECT count(case when "Traffic_Type" != \'None\' or "prediction" != \'None\' then 1 end) as Total, count(case when ("Traffic_Type" != \'None\' or "prediction" != \'None\') and "Traffic_Type" = "prediction" then 1 end) as RightPredictions from DATAIKU_DATABASE.DATAIKU_SCHEMA.TEXAS_EVENTS_2017_SCORED_WEATHERTRAFFICEVENTS;')

Total = [row[0] for row in success_rate][0]

Sucess = [row[1] for row in success_rate][0]

st.write("Sucess rate = " + str(Sucess/Total))






# total_events_in_texas = run_query('SELECT DATE_TRUNC(day,"StartTime_Weather") as "Days", count(case when "Traffic_Type" != \'None\' then 1 end) as real_events, count(case when "prediction" != \'None\' then 1 end) as predicted_events from DATAIKU_DATABASE.DATAIKU_SCHEMA.TEXAS_EVENTS_2020_SCORED_WEATHERTRAFFICEVENTS group by "Days" order by "Days";')

# days = [row[0] for row in total_events_in_texas]

# traffic = [row[1] for row in total_events_in_texas]

# prediction = [row[2] for row in total_events_in_texas]

# col1, col2= st.columns(2)

# with col1:
#     fig, ax = plt.subplots()
#     ax.xaxis.set_major_locator(mdates.YearLocator())
#     ax.xaxis.set_minor_locator(mdates.MonthLocator())
#     ax.xaxis.set_label_text("Year")
#     ax.yaxis.set_label_text("Events")

#     ax.set_title('Total Daily Texas Traffic Events During Weather Events in 2017 (real)', fontstyle='italic')

#     ax.plot(days, traffic)

#     figure(figsize=(160, 6), dpi=160)

#     st.pyplot(fig)

# with col2:
#     fig, ax = plt.subplots()
#     ax.xaxis.set_major_locator(mdates.YearLocator())
#     ax.xaxis.set_minor_locator(mdates.MonthLocator())
#     ax.xaxis.set_label_text("Year")
#     ax.yaxis.set_label_text("Events")

#     ax.set_title('Total Daily Texas Traffic Events During Weather Events in 2017 (Prediction)', fontstyle='italic')

#     ax.plot(days, prediction)

#     figure(figsize=(160, 6), dpi=160)

#     st.pyplot(fig)


# fig, ax = plt.subplots()
# ax.xaxis.set_major_locator(mdates.YearLocator())
# ax.xaxis.set_minor_locator(mdates.MonthLocator())
# ax.xaxis.set_label_text("Year")
# ax.yaxis.set_label_text("Events")

# ax.set_title('Total Daily Texas 2017 Traffic Events During Weather Events Comparation', fontstyle='italic')

# ax.plot(days, traffic)
# ax.plot(days, prediction)

# figure(figsize=(160, 6), dpi=160)

# st.pyplot(fig)