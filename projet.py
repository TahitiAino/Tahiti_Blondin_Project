
import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import time
from functools import wraps
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.express as px
import altair as alt


#Function to load the data from the csv
@st.cache(allow_output_mutation=True)
def load_data(nrows, filename, number):

    req_col=['date_mutation','nature_mutation','valeur_fonciere','code_postal','nom_commune','type_local','surface_reelle_bati','nombre_pieces_principales','nature_culture','surface_terrain','longitude','latitude']
    data=pd.read_csv(filename,nrows=number,usecols=req_col,parse_dates=['date_mutation'],dtype={("nature_mutation ","nom_commune","nature_culture"):"category",("valeur_fonciere","surface_relle_bati","nombre_pieces_principales","surface_terrain","longitude","latitude","code_postal") : "float32"})
    data['date_mutation']=pd.to_datetime(data["date_mutation"])
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)

    return data



#Function to have the log time on a file
def log_time(func):
    def wrapper(*args,**kwargs):

        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        timeTaken = end - start

        ts = time.time()

        d = open("timeOfLogOnFile.txt", 'a')
        d.write("It took "+ str(timeTaken)+" seconds \n\n")
        d.write("The timestamp is "+ str(ts)+"\n\n")
        d.close()

    return wrapper


#Function to count rows for the heat map
def count_rows(rows): 
    return len(rows)


#Function to see datas on a map
@log_time
def mapping_data(dataset,col):
    st.subheader('Visualize data on the map')
    st.write('Please choose a month :')
    month_to_filter = st.slider('month', 1, 11, 2)
    filtered_data = dataset[dataset[col].dt.month == month_to_filter]
    st.write('Map des valeurs foncières le %seme mois' % month_to_filter)
    st.map(filtered_data)


#Function that takes the dataframe and returns a dataframe with longitude, latitude and its date of mutation without null values (with which we can't use st.map())
def filterLonLatForMapping(df): 
    dt= [df["latitude"], df["longitude"], df["date_mutation"]]

    headers = ["latitude", "longitude", "date_mutation"]
    datanew1 = pd.concat(dt, axis=1, keys=headers)
    datanew = datanew1.dropna()
    return datanew
    
#Function to put values in a bar chart
def charting(df): 
    fig = px.bar(x=df['nom_commune'], y=[df['valeur_fonciere'], df['surface_terrain']], barmode='group', height=400)

    return fig


def bar_chart_local_commune_valeur(df):
    st.subheader("Each data with their type of local as well as their nature of mutation")
    dt= [df["type_local"], df["nature_mutation"]]
    headers = ["type_local", "nature_mutation"]
    chart_data = pd.concat(dt, axis=1, keys=headers)
    chart_data = chart_data.dropna()
    st.bar_chart(chart_data)

def plotly_bar_chart(df):
    
    this_chart = go.Figure(
        data=[go.Bar(x=df['nom_commune'], y=df['valeur_fonciere'], text = df['valeur_fonciere'],textposition = 'auto')])
    return this_chart

#Function to obatin a heat map
def heat_m(grouped_data):
    fig, ax = plt.subplots()
    sns.heatmap(grouped_data, center=0)
    st.write(fig)

def get_dom(dt): 
    return dt.day 

#Function to obtain the month
def get_month(dat): 
    return dat.month

def toTime(dataset, col):
    dataset[col]= pd.to_datetime(dataset[col])


#Function to obatin the total number of mutations by days or months
def numMutations(data, DATE_COLUMN):
    st.subheader('Total number of mutations')
    st.write('Visualize number of mutations by :')
    selectday = st.checkbox('day')
    selectmonth = st.checkbox('month')
    if selectday:
        st.subheader('Days')
        hist_values = np.histogram(data[DATE_COLUMN].dt.day, bins=31, range=(1,31))[0]
        st.bar_chart(hist_values)

    if selectmonth:
        st.subheader('Months')
        hist_values = np.histogram(data[DATE_COLUMN].dt.month, bins=12, range=(1,12))[0]
        st.bar_chart(hist_values)


#Function to see the top communes by their real estate values
def estateValuesCom(data, number):
    st.subheader('Real estate values by communes')
    v2 = data.groupby('nom_commune').agg({'valeur_fonciere': 'mean'}).reset_index()
    v2 = v2.sort_values(by=['valeur_fonciere'], ascending=False)

    st.write('Top ' , number , ' of real estate value by commune')
    chart = plotly_bar_chart(v2.head(number))
    st.plotly_chart(chart, use_container_width=True)
    st.write('Visualize communes with the lowest prices by square meter ?')
    estatechoice = st.checkbox('yes !')
    if estatechoice:
        chartbis = plotly_bar_chart(v2.tail(number))
        st.plotly_chart(chartbis, use_container_width=True)

#Function to see the top communes by their square meters' prices
def squareMeterCom(data, number):
    st.subheader('Top of communes with their prices by square meter')
    st.write('Top ' , number , ' of communes with the highest prices by square meter')

    v3 = data.groupby('nom_commune').agg({'surface_terrain': 'mean', 'valeur_fonciere': 'mean'}).reset_index()

    v3['diff'] = v3['valeur_fonciere'] - v3['surface_terrain']
    v6 = v3.sort_values(by=['diff'], ascending=False)
    dft1 = v6.set_index('nom_commune')
    st.line_chart(dft1.head(number))

    v3['diff'] = v3['valeur_fonciere'] - v3['surface_terrain']
    v3 = v3.sort_values(by=['diff'], ascending=False)
    chart2 = charting(v3.head(number))
    st.plotly_chart(chart2)

    st.write('Visualize communes with the lowest prices by square meter ?')
    meterchoice = st.checkbox('yes')
    if meterchoice:
        st.write('Top ' , number , ' des communes au mètre carré le moin cher')
        st.write('Line graph version')
        st.line_chart(dft1.tail(number))

        st.write('Histrogram version')
        chart4 = charting(v3.tail(number))
        st.plotly_chart(chart4)

#Function to see the top communes by their types of transaction
def comByTypeOfTrans(data, number):
    st.subheader('Top of communes with their types of transactions')
    v4 = data.groupby(['nom_commune','nature_mutation']).apply(count_rows).unstack()
    heat_m(v4)


#Function to see the communes by their number real estates transactions
def comByRealEstate(data, number):
    st.subheader('Top of communes by their number of real estate transactions')
    v5 = data.groupby(['nom_commune']).size().reset_index(name = 'count')
    v5 = v5.sort_values(by=['count'], ascending=False)
    v5head = v5.head(number)
    v5tail = v5.tail(number)

    st.write('Top ' , number , ' of communes with the most real estate transactions')
    input_col, pie_col = st.columns(2)
    fig = px.pie(v5head, values = "count", names = "nom_commune", title = 'Top of communes with the most real estate transactions')
    fig.update_layout(width = 500, height = 500, margin = dict(l=50, r=50, b=50, t=50))
    pie_col.write(fig)
    st.write('Visualize top ', number, ' communes with the less real estate transactions ?')
    transactionchoice = st.checkbox('yes :)')
    input_col2, pie_col2 = st.columns(2)

    if transactionchoice:
        fig2 = px.pie(v5tail, values = "count", names = "nom_commune", title = 'Top of communes with the less real estate transactions')
        fig2.update_layout(width = 500, height = 500, margin = dict(l=50, r=50, b=50, t=50))
        pie_col2.write(fig2)

#Function to see the scatter plot
def scatterPlot(data):
    xChoice = list(data.select_dtypes(['float','int']).columns)
    columns_choice = list(data[['month','valeur_fonciere','code_postal','surface_terrain','nombre_pieces_principales','surface_reelle_bati']])

    st.subheader('Scatter plot : Please choose the X and Y axis parameters')
    xVal = st.selectbox('X axis', options=xChoice)
    yVal = st.selectbox('Y axis', options=columns_choice)

    plot = px.scatter(data_frame=data, x=xVal,y=yVal)
    st.plotly_chart(plot)

def main():
    
    dfOption = pd.DataFrame({'first column': ["2016", "2017", "2018", "2019", "2020"],})

 
    option = st.sidebar.selectbox('Which year would you like to study?',dfOption['first column'])
 


    if option == "2016":
        st.title('Data visualization for the year 2016')
        filename = r"full_2016.csv"
        DATE_COLUMN = "date_mutation"
    elif option == '2017':
        st.title('Data visualization for the year 2017')
        filename = r"full_2017.csv"
        DATE_COLUMN = "date_mutation"
    elif option == '2018':
        st.title('Data visualization for the year 2018')
        filename = r"full_2018.csv"
        DATE_COLUMN = "date_mutation"
    elif option == '2019':
        st.title('Data visualization for the year 2019')
        filename = r"full_2019.csv"
        DATE_COLUMN = "date_mutation"
    elif option == '2020':
        st.title('Data visualization for the year 2020')
        filename = r"full_2020.csv"
        DATE_COLUMN = "date_mutation"


    number = st.slider('How many rows do you want?', 10, 10000, 25)
 
    data_load_state = st.text('Loading data...')
    data = load_data(10000, filename, number)
    data_load_state.text(" ")
    if st.checkbox('Show raw data'):
        st.subheader('Raw data')
        st.write(data)

    toTime(data,"date_mutation")

    numMutations(data, DATE_COLUMN)

    st.subheader('Option to choose the top of communes you want to see')
    number = st.number_input('Le top combien de commune voulez vous voir ?', value=5)

    estateValuesCom(data, number)
    squareMeterCom(data, number)
    comByTypeOfTrans(data, number)
    comByRealEstate(data, number)

    data['month']= data['date_mutation'].map(get_month)

    scatterPlot(data)
    mapping_data(filterLonLatForMapping(data), "date_mutation") #we map the data with the function mapping data, with parameters the function filterLonLatForMapping that takes the dataframe and return longitude and latitude without null values (with which we can't use st.map()) and our column date of mutation that will be used to choose the month we want to display on the map.
    bar_chart_local_commune_valeur(data)

if __name__ == "__main__":
    main()

