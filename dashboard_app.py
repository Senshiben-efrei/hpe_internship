# create a streamlit app
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import scipy as sp

def computeBacklog(backlog):
    # change the date columns to datetime Actual Delivery Date (Item) and HPE Received Date
    backlog['Actual Delivery Date (Item)'] = pd.to_datetime(backlog['Actual Delivery Date (Item)'])
    backlog['HPE Received Date'] = pd.to_datetime(backlog['HPE Received Date'])

    # calculate the the time between the HPE Received Date and the Actual Delivery Date (Item)
    backlog['time_to_ship'] = backlog['Actual Delivery Date (Item)'] - backlog['HPE Received Date'] 

    # convert the time to days
    backlog['time_to_ship'] = backlog['time_to_ship'].dt.days/5

    # drop rows where time_to_ship is inf or nan
    backlog = backlog[backlog['time_to_ship'] != np.inf]
    backlog = backlog[backlog['time_to_ship'].notna()]

    # create a new column called 'shiped to' and assign the value of the column 'Ship To Name'
    backlog['shiped_to'] = backlog['Ship To Name']

    # if of shiped_to contains 'disway' or 'disty' then change the value to it
    backlog.loc[backlog['shiped_to'].str.contains('disway', case=False), 'shiped_to'] = 'disway'
    backlog.loc[backlog['shiped_to'].str.contains('disty', case=False), 'shiped_to'] = 'disty'

    

    # save the modified data into session state
    st.session_state.backlog = backlog


def dataOverview(backlog):    
    # display the data
    st.title("Data Overview")
    st.write(backlog.head())

    # create 2 columns
    col1, col2 = st.columns(2)

    # plot delevery type with plotly pie chart
    delivery_type = backlog['Delivery Type'].value_counts()
    fig = go.Figure(data=[go.Pie(labels=delivery_type.index, values=delivery_type.values)])
    fig.update_layout(title='Delivery Type')
    col2.plotly_chart(fig)

    # plot Item Status with plotly pie chart hide percentage
    item_status = st.session_state.backlog_backup['Item Status'].value_counts()
    fig = go.Figure(data=[go.Pie(labels=item_status.index, values=item_status.values)])
    fig.update_traces(textposition='inside')
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')
    fig.update_layout(title='Item Status')
    col1.plotly_chart(fig)

    # plot missing values sorted by percentage with plotly horizontal bar chart
    missing = backlog.isnull().sum().sort_values(ascending=True)
    missing = missing[missing > 0]
    missing = missing/len(backlog)
    missing = missing*100
    fig = go.Figure(go.Bar(x=missing, y=missing.index, orientation='h'))
    fig.update_layout(title='Missing Values', xaxis_title='Percentage')
    col1.plotly_chart(fig)

    # plot Ship to name with plotly pie chart hide percentage change color
    ship_to_name = backlog['shiped_to'].value_counts()
    fig = go.Figure(data=[go.Pie(labels=ship_to_name.index, values=ship_to_name.values)])
    fig.update_traces(textposition='inside')
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')
    fig.update_layout(title='Ship to Name')
    st.plotly_chart(fig)
    
    # plot delivery time displot with seaborn
    # size
    fig, ax = plt.subplots(figsize=(10, 7))
    sns.distplot(backlog['time_to_ship'], ax=ax)
    ax.set_title('Delivery Time')
    col2.pyplot(fig)

    # create other 2 columns
    col3, col4 = st.columns(2)

    # plot on globe lines between ship to and ship from with plotly
    # create a dataframe with the ship to and ship from coordinates
    # find the coordinates of the ship to using the geopy library
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="hpe_app")
    ship_to = backlog['Ship To Country'].unique()
    ship_to = pd.DataFrame(ship_to, columns=['ship_to'])
    ship_to['location'] = ship_to['ship_to'].apply(geolocator.geocode)
    ship_to['point'] = ship_to['location'].apply(lambda loc: tuple(loc.point) if loc else None)
    ship_to[['latitude', 'longitude', 'altitude']] = pd.DataFrame(ship_to['point'].tolist(), index=ship_to.index)
    ship_to = ship_to.drop(['location', 'point', 'altitude'], axis=1)

    # find the coordinates of the ship from using the geopy library
    ship_from = backlog['CoO Name (Country of Origin)'].unique()
    ship_from = pd.DataFrame(ship_from, columns=['ship_from'])
    ship_from['location'] = ship_from['ship_from'].apply(geolocator.geocode)
    ship_from['point'] = ship_from['location'].apply(lambda loc: tuple(loc.point) if loc else None)
    ship_from[['latitude', 'longitude', 'altitude']] = pd.DataFrame(ship_from['point'].tolist(), index=ship_from.index)
    ship_from = ship_from.drop(['location', 'point', 'altitude'], axis=1)
    # add the count of the ship from based on the backlog
    ship_from['count'] = ship_from['ship_from'].apply(lambda x: backlog[backlog['CoO Name (Country of Origin)'] == x]['CoO Name (Country of Origin)'].count())
    # write only ship from and count 
    ship_from_count = ship_from[['ship_from', 'count']]

    # pie chart of the ship from count
    fig = go.Figure(data=[go.Pie(labels=ship_from_count['ship_from'], values=ship_from_count['count'])])
    fig.update_traces(textposition='inside')
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')
    fig.update_layout(title='Ship From')
    col3.plotly_chart(fig)


    # color list 
    colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#000000']

    
    # plot the lines on the globe
    fig = go.Figure()
    for i in range(len(ship_to)):
        for j in range(len(ship_from)):
            fig.add_trace(go.Scattergeo(
                locationmode = 'country names',
                lon = [ship_to['longitude'][i], ship_from['longitude'][j]],
                lat = [ship_to['latitude'][i], ship_from['latitude'][j]],
                mode = 'lines',
                line = dict(width = 3,color = colors[j]),
                opacity = 1,
                name = str(ship_to['ship_to'][i]) + ' - ' + str(ship_from['ship_from'][j])
            ))
    fig.update_layout(
        title_text = 'Ship To - Ship From',
        showlegend = False,
        geo = dict(
            scope = 'world',
            projection_type = 'natural earth'
        )
    )
    col4.plotly_chart(fig)





def computeHitBundles(backlog, hitbundles, orderable, equivalent):
    # create a cross dataframe with the hitbundles and the backlog
    orderable = backlog.copy()
    orderable = orderable[orderable['Product Number'].isin(hitbundles['Parts ID'])]

    # add the orderable november FY23 to the orderable dataframe
    orderable = orderable.merge(hitbundles, left_on='Product Number', right_on='Parts ID', how='left')

    # assign for each unique product number a category id 
    orderable['category_id'] = orderable.groupby('Product Number').ngroup()

    # drop the first row of equivalent
    equivalent = equivalent.drop(equivalent.index[0])

    # add the Unnamed: and the Unnamed: 7 column to the orderable dataframe join by Unnamed: 2 and product number
    orderable = orderable.merge(equivalent, left_on='Product Number', right_on='Unnamed: 2', how='left')

    # for each product number if unamed: 7 is not nan then assign the category id of this row to the category id of the row with the product number equal to unamed: 7
    for index, row in orderable.iterrows():
        if pd.notnull(row['Unnamed: 6']):
            orderable.loc[orderable['Product Number'] == row['Unnamed: 6'], 'category_id'] = row['category_id']

    # save the modified data into session state
    st.session_state.orderable = orderable

# def computeAruba(backlog, aruba, orderable_aruba):
#     # create a cross dataframe with the hitbundles and the backlog
#     orderable_aruba = backlog.copy()
#     orderable_aruba = orderable_aruba[orderable_aruba['Product Number'].isin(aruba['PartID'])]

#     # add the orderable november FY23 to the orderable dataframe
#     orderable_aruba = orderable_aruba.merge(aruba, left_on='Product Number', right_on='PartID', how='left')

#     # assign for each unique product number a category id 
#     orderable_aruba['category_id'] = orderable_aruba.groupby('Product Number').ngroup()

#     # for each product number if unamed: 0 is not nan or Replaced then assign the category id of this row to the category id of the row with the product number equal to PartID
#     for index, row in orderable_aruba.iterrows():
#         if pd.notnull(row['Unnamed: 0']) or row['Unnamed: 0'] == 'Replaced':
#             orderable_aruba.loc[orderable_aruba['Product Number'] == row['Unnamed: 0'], 'category_id'] = row['category_id']

#     # save the modified data into session state
#     st.session_state.orderable_aruba = orderable_aruba
    

def hitBundles(backlog, hitbundles, orderable):

    

    # display the data
    st.title("Hit Bundles")
    st.write(backlog.head())
    st.write(hitbundles.head())
    st.write(orderable.head())
    st.write(orderable.shape)

    # box plot of product description and time to ship vertical
    fig = px.box(orderable, y='Product Description', x='time_to_ship', orientation='h', color='Product Description')
    fig.update_layout(title='Delivery Time', height=3000)
    st.plotly_chart(fig)

    # create 2 columns
    col1, col2 = st.columns(2)

    # find the list of all columns names that contain the word 'Orderable'
    orderable_columns = [col for col in orderable.columns if 'Orderable' in col]

    # select the orderable month
    orderable_month = col2.selectbox('Select the orderable month', orderable_columns)

    # make a temp dataframe with the unique product description and the orderable november FY23\
    temp = orderable[['Product Number','Product Description', orderable_month,'Unnamed: 6','Unnamed: 7', 'category_id']].drop_duplicates()

    def color_orderable(s):
        color = '#01A982' if s == 'YES' else '#C54E4B'
        return f'background-color: {color}'


    # st data frame with the temp dataframe
    col2.write('List of all servers and orderable state')
    col2.dataframe(temp.style.applymap(color_orderable, subset=[orderable_month]))


    # plot pie chart of sold servers in orderable
    sold_servers = orderable['Product Description'].value_counts()
    fig = go.Figure(data=[go.Pie(labels=sold_servers.index, values=sold_servers.values)])
    fig.update_traces(textposition='inside')
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')
    fig.update_layout(title='Sold Servers')
    col1.plotly_chart(fig)
    
    # bar plot of sold servers in orderable divided by Orderable November FY23
    fig = px.histogram(orderable, y='Product Description', color=orderable_month, color_discrete_map={'YES': '#01A982', 'NO': '#C54E4B'})
    fig.update_layout(title='Product Description')
    col1.plotly_chart(fig)

    # text input for product description
    product_number = col2.text_input('Input Product Number', placeholder='Example : P16926-421')
    # submit button
    submit = col2.button('Submit')

    # if submit button is pressed
    if submit or product_number:
        # if the text input is is surronded by quotes remove them
        if product_number[0] == '"' and product_number[-1] == '"':
            product_number = product_number[1:-1]

        # write the mean time to ship for product_number
        col2.write('Average delivery time : ' + str(orderable[orderable['Product Number'] == product_number]['time_to_ship'].mean()))

        # write sold units for product_number
        col2.write('Sold units : ' + str(orderable[orderable['Product Number'] == product_number]['Product Number'].value_counts()[product_number]))

        # colored text of orderable november fy23 green if yes red if no
        if orderable[orderable['Product Number'] == product_number][orderable_month].values[0] == 'YES':
            col2.markdown('<span style="color:green">Orderable</span>', unsafe_allow_html=True)
        else:
            col2.markdown('<span style="color:red">Not Orderable</span>', unsafe_allow_html=True)

        # plot line plot of time to ship for product_number
        fig = px.scatter(orderable[orderable['category_id'] == orderable[orderable['Product Number'] == product_number]['category_id'].values[0]], x='HPE Received Date', y='time_to_ship', color='Product Description')
        fig.update_layout(title='Delivery Time')
        col2.plotly_chart(fig)

def sales(backlog, orderable):
    # title
    st.title("Sales Analysis")
    # select product type all or servers
    product_type = st.selectbox('Product Type', ['All', 'Servers'])
    
    # select shiped_to to study and all
    shiped_to = st.multiselect('Select Shiped To', ['All'] + backlog['shiped_to'].unique().tolist(), default=['All'])
    # if a shiped_to is selected
    if 'All' in shiped_to:
        if product_type == 'All':
            # slect the entire data
            backlog = backlog[backlog['shiped_to'].isin(backlog['shiped_to'].unique())]
            st.write(backlog.shape)
        elif product_type == 'Servers':
            orderable = orderable
            st.write(orderable.shape)
    else:
        # filter the data
        if product_type == 'All':
            backlog = backlog[backlog['shiped_to'].isin(shiped_to)]
            st.write(backlog.shape)
        elif product_type == 'Servers':
            orderable = orderable[orderable['shiped_to'].isin(shiped_to)]
            st.write(orderable.shape)


    # # chose a date range
    if product_type == 'All':
    #     # select a year by comparing the min and max of the HPE Received Date 
    #     year = st.selectbox('Select Year', [str(i) for i in range(backlog['HPE Received Date'].min().year, backlog['HPE Received Date'].max().year + 1)])

    #     # select a quarter by comparing the min and max of the HPE Received Date
    #     quarter = st.selectbox('Select Quarter', ['All'] + [str(i) for i in range(1, 5)])

    #     # if quarter is all
    #     if quarter == 'All':
    #         # filter the data
    #         backlog = backlog[backlog['HPE Received Date'].dt.year == int(year)]
    #     else:
    #         # filter the data
    #         backlog = backlog[(backlog['HPE Received Date'].dt.year == int(year)) & (backlog['HPE Received Date'].dt.quarter == int(quarter))]
    # elif product_type == 'Servers':
    #     # select a year by comparing the min and max of the HPE Received Date
    #     year = st.selectbox('Select Year', [str(i) for i in range(orderable['HPE Received Date'].min().year, orderable['HPE Received Date'].max().year + 1)])

    #     # select a quarter by comparing the min and max of the HPE Received Date
    #     quarter = st.selectbox('Select Quarter', ['All'] + [str(i) for i in range(1, 5)])

    #     # if quarter is all
    #     if quarter == 'All':
    #         # filter the data
    #         orderable = orderable[orderable['HPE Received Date'].dt.year == int(year)]
    #     else:
    #         # filter the data
    #         orderable = orderable[(orderable['HPE Received Date'].dt.year == int(year)) & (orderable['HPE Received Date'].dt.quarter == int(quarter))]


        date_range = st.date_input('Select Date Range', [backlog['HPE Received Date'].min(), backlog['HPE Received Date'].max()])
        # transform the date range to datetime
        date_range = [pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])]
        # filter the data
        backlog = backlog[(backlog['HPE Received Date'] >= date_range[0]) & (backlog['HPE Received Date'] <= date_range[1])]
    elif product_type == 'Servers':
        date_range = st.date_input('Select Date Range', [orderable['HPE Received Date'].min(), orderable['HPE Received Date'].max()])
        # transform the date range to datetime
        date_range = [pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])]
        # filter the data
        orderable = orderable[(orderable['HPE Received Date'] >= date_range[0]) & (orderable['HPE Received Date'] <= date_range[1])]

    # create 2 columns
    col1, col2 = st.columns(2)

    # create other 2 columns
    col3, col4 = st.columns(2)


    if product_type == 'All':
        # write data frame with the product description product number and the sold units and the average time to ship
        col2.write('Product Description, Product Number, Sold Units, Average Time to Ship')
        col2.dataframe(backlog.groupby(['Product Description', 'Product Number']).agg({'Product Number': 'count', 'time_to_ship': 'mean'}).rename(columns={'Product Number': 'Sold Units', 'time_to_ship': 'Average Time to Ship'}).reset_index())
    elif product_type == 'Servers':
        col2.dataframe(orderable.groupby(['Product Description', 'Product Number']).size().reset_index(name='sold units'))

    # bar plot of product description
    if product_type == 'All':
        product_number = backlog['Product Description'].value_counts()
    elif product_type == 'Servers':
        product_number = orderable['Product Description'].value_counts()
    
    # chose how many values to display
    num = col1.slider('Number of Values to Display', 1, len(product_number), 10)

    # plot the bar plot
    fig = go.Figure(go.Bar(x=product_number.index[:num], y=product_number.values[:num]))
    fig.update_layout(title='Product Description')
    col1.plotly_chart(fig)

    # box plot of time to ship of these values for the num of values
    # temporary data frame of num of values
    if product_type == 'All':
        temp = backlog[backlog['Product Description'].isin(product_number.index[:num])]
    elif product_type == 'Servers':
        temp = orderable[orderable['Product Description'].isin(product_number.index[:num])]
    # plot the box plot sorted by quantity
    fig = px.box(temp, x='Product Description', y='time_to_ship', color='Product Description', points='all')
    fig.update_layout(title='Delivery Time')
    st.plotly_chart(fig)

    
    # find the list of all columns names that contain the word 'Orderable'
    orderable_columns = [col for col in orderable.columns if 'Orderable' in col]

    # select the orderable month
    orderable_month = col1.selectbox('Select the orderable month', orderable_columns)

    # make a temp dataframe with the unique product description and the orderable november FY23\
    temp = orderable[['Product Number', 'Proliant Type', 'Generation','Product Description', orderable_month,'Unnamed: 6','Unnamed: 7', 'category_id']].drop_duplicates()
    # add the sold units of this product number to the temp dataframe
    temp = temp.merge(orderable.groupby('Product Number').size().reset_index(name='sold units'), on='Product Number', how='left')
    # add the time to ship to the temp dataframe
    temp = temp.merge(orderable.groupby('Product Number')['time_to_ship'].mean().reset_index(name='time_to_ship'), on='Product Number', how='left')
    # add the sold units to the temp dataframe
    # in Generation remove spaces
    temp['Generation'] = temp['Generation'].str.replace(' ', '')


    def color_orderable(s):
        color = '#01A982' if s == 'YES' else '#C54E4B'
        return f'background-color: {color}'

    def color_proliant(s):
        # find orderable unnamed 0 unique values
        orderable_unnamed_0 = orderable['Proliant Type'].unique()
        color_list = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080']
        # create a list of colors the same length as the unique values
        color = [color_list[i] for i in range(len(orderable_unnamed_0))]
        # create a dictionary of the unique values and the colors
        color_dict = dict(zip(orderable_unnamed_0, color))
        # return the color of the value
        return f'background-color: {color_dict[s]}'

    
    def color_generation(s):
        # find orderable unnamed 0 unique values
        orderable_unnamed_0 = orderable['Generation'].unique()
        color_list = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080']
        # create a list of colors the same length as the unique values
        color = [color_list[i] for i in range(len(orderable_unnamed_0))]
        # create a dictionary of the unique values and the colors
        color_dict = dict(zip(orderable_unnamed_0, color))
        # return the color of the value
        return f'background-color: {color_dict[s]}'



    # st data frame with the temp dataframe
    col1.write('List of all servers and orderable state')
    col1.dataframe(temp.style.applymap(color_orderable, subset=[orderable_month]).applymap(color_proliant, subset=['Proliant Type']).applymap(color_generation, subset=['Generation']))


    
    # text input for product description
    product_number = col2.text_input('Input Product Number', placeholder='Example : P16926-421')
    # submit button
    submit = col2.button('Submit')

    # if submit button is pressed
    if submit or product_number:
        # if the text input is is surronded by quotes remove them
        if product_number[0] == '"' and product_number[-1] == '"':
            product_number = product_number[1:-1]

        if product_type == 'All':
            # write the product description
            col2.write('Product Description : ' + backlog[backlog['Product Number'] == product_number]['Product Description'].values[0])

            # write the mean time to ship for product_number
            col2.write('Average delivery time : ' + str(backlog[backlog['Product Number'] == product_number]['time_to_ship'].mean()))

            # write sold units for product_number
            col2.write('Sold units : ' + str(backlog[backlog['Product Number'] == product_number]['Product Number'].value_counts()[product_number]))

        else:
            # write the product description
            col2.write('Product Description : ' + orderable[orderable['Product Number'] == product_number]['Product Description'].values[0])

            # write the mean time to ship for product_number
            col2.write('Average delivery time : ' + str(orderable[orderable['Product Number'] == product_number]['time_to_ship'].mean()))

            # write sold units for product_number
            col2.write('Sold units : ' + str(orderable[orderable['Product Number'] == product_number]['Product Number'].value_counts()[product_number]))

            # colored text of orderable november fy23 green if yes red if no
            if orderable[orderable['Product Number'] == product_number][orderable_month].values[0] == 'YES':
                col2.markdown('<span style="color:green">Orderable</span>', unsafe_allow_html=True)
            else:
                col2.markdown('<span style="color:red">Not Orderable</span>', unsafe_allow_html=True)
                # if there is a replacement product write it
                #if orderable[orderable['Product Number'] == product_number]['Unnamed: 6'].values[0] != 'nan':
                    #col2.write('Replacement Product : ' + orderable[orderable['Product Number'] == product_number]['Unnamed: 6'].values[0] + ' ' + orderable[orderable['Product Number'] == product_number]['Unnamed: 7'].values[0])
                    
            # write a table of product stats Core GHZ Nbr Processor RAM Alimentation
            col2.write('Product Info')
            col2.dataframe(orderable[orderable['Product Number'] == product_number][['Core', 'GHZ', 'Nbr Processor', 'RAM', 'Alimentation', 'LFF/SFF']].drop_duplicates())
            # check if the product number replacement product has a replacement product
            if orderable[orderable['Product Number'] == product_number]['Unnamed: 6'].values[0] != 'nan':
                # if it does write the replacement product info
                col2.write('Replacement Product Info')
                #col2.dataframe(orderable[orderable['Product Number'] == orderable[orderable['Product Number'] == product_number]['Unnamed: 6'].values[0]][['Core', 'GHZ', 'Nbr Processor', 'RAM', 'Alimentation', 'LFF/SFF']].drop_duplicates())

            # plot line plot of time to ship for product_number 
            fig = px.scatter(orderable[orderable['category_id'] == orderable[orderable['Product Number'] == product_number]['category_id'].values[0]], x='HPE Received Date', y='time_to_ship', color='Product Description')
            fig.update_layout(title='Delivery Time')
            col2.plotly_chart(fig)

            # plot number of sold units for product_number histogram in this date range 
            fig = px.histogram(orderable[orderable['category_id'] == orderable[orderable['Product Number'] == product_number]['category_id'].values[0]], x='HPE Received Date', color='Product Description')
            fig.update_layout(title='Sold Units')
            fig.update_layout(bargap=0.1)
            col2.plotly_chart(fig)


    # write in a dataframe each proliant type and the average time to ship for that type in the selected time range
    col1.write('Average delivery time per Proliant Type')
    col1.dataframe(temp.groupby('Proliant Type')['time_to_ship'].mean().reset_index().sort_values('time_to_ship', ascending=False).style.applymap(color_proliant, subset=['Proliant Type']))

    # write in a dataframe each generation and the average time to ship for that generation of each proliant type
    col1.write('Average delivery time per Generation')
    col1.dataframe(temp.groupby(['Proliant Type', 'Generation'])['time_to_ship'].mean().reset_index().sort_values('time_to_ship', ascending=False).style.applymap(color_proliant, subset=['Proliant Type']).applymap(color_generation, subset=['Generation']))



    # # write orderavle aruba
    # st.write('Orderable Aruba')
    # # write the orderable aruba dataframe unique product number and unnamed 0
    # st.dataframe(st.session_state.orderable_aruba[['Product Number', 'Unnamed: 0', 'category_id']].drop_duplicates())
    









# run the app
if __name__ == '__main__':
    # set to wide mode
    st.set_page_config(layout="wide")

    # create a sidebar
    st.sidebar.title('Dashboard')
    st.sidebar.subheader('Upload Data')
    # create a file uploader
    file = st.sidebar.file_uploader('Upload Backlog', type=['xlsx'])
    # create a placeholder
    placeholder = st.sidebar.empty()
    placeholder.info(' Please Submit Data', icon='📑')
    # create a button
    button = st.sidebar.button('Submit Backlog')
    # on click of button
    if button:
        #check if file is uploaded
        if file is not None:
            # set the placeholder
            placeholder.warning(' Loading Data...', icon='⌛')
            # store the data in a dataframe in the session state
            st.session_state.backlog_backup = pd.read_excel(file)
            # update the sidebar
            placeholder.success(' Successfuly uploaded the backlog ', icon='✔️')
            # Calling the function `computeBacklog` with the argument
            # `st.session_state.backlog_backup`
            # computeBacklog(st.session_state.backlog_backup)
        else:
            placeholder.error(' Please upload a file', icon='❌')
    
    if 'backlog_backup' in st.session_state:
        # make a checklist to choose countries from the list of Ship To Country
        countries = st.sidebar.multiselect('Choose countries', st.session_state.backlog_backup['Ship To Country'].unique(), default=['MA'])
        if countries:
            # filter the backlog with the countries store it in a copy
            backlog = st.session_state.backlog_backup[st.session_state.backlog_backup['Ship To Country'].isin(countries)]
            computeBacklog(backlog)
            if 'hitbundles' in st.session_state:
                computeHitBundles(st.session_state.backlog, st.session_state.hitbundles, st.session_state.orderable, st.session_state.equivalent)
            # if 'aruba' in st.session_state:
            #     computeAruba(st.session_state.backlog, st.session_state.aruba, st.session_state.orderable_aruba)
    # check if backlog is defined
    if 'backlog' in st.session_state:
        placeholder.success(' Successfuly uploaded the backlog ', icon='✔️')

        # create a separator
        st.sidebar.markdown('---')
        # create a second file uploader for hit bundles
        file2 = st.sidebar.file_uploader('Upload Hit Bundles', type=['xlsx'])
        # create a placeholder2
        placeholder2 = st.sidebar.empty()
        placeholder2.info(' Please Submit Data', icon='📑')
        # create a button
        button2 = st.sidebar.button('Submit Hit Bundles')
        # on click of button
        if button2:
            #check if file is uploaded
            if file2 is not None:
                # set the placeholder2
                placeholder2.warning(' Loading Data...', icon='⌛')
                # store the data in a dataframe in the session state
                st.session_state.hitbundles = pd.read_excel(file2)
                st.session_state.equivalent = pd.read_excel(file2, sheet_name='Equivalent')
                # initialize the orderable dataframe to backlog
                st.session_state.orderable = st.session_state.backlog.copy()
                # update the sidebar
                placeholder2.success(' Successfuly uploaded the hit bundles ', icon='✔️')
                computeHitBundles(st.session_state.backlog, st.session_state.hitbundles, st.session_state.orderable, st.session_state.equivalent)
            else:
                placeholder2.error(' Please upload a file', icon='❌')

        # check if hitbundles is defined
        if 'hitbundles' in st.session_state:
            placeholder2.success(' Successfuly uploaded the hit bundles ', icon='✔️')

            # create a separator
            st.sidebar.markdown('---')
            # create a third file uploader for aruba updates
            file3 = st.sidebar.file_uploader('Upload Aruba Updates', type=['xlsx'])
            # create a placeholder3
            placeholder3 = st.sidebar.empty()
            placeholder3.info(' Please Submit Data', icon='📑')
            # create a button
            button3 = st.sidebar.button('Submit Aruba Updates')
            # on click of button
            if button3:
                #check if file is uploaded
                if file3 is not None:
                    # set the placeholder3
                    placeholder3.warning(' Loading Data...', icon='⌛')
                    # store the data in a dataframe in the session state
                    st.session_state.aruba = pd.read_excel(file3)
                    # initialize the orderable dataframe to backlog
                    # st.session_state.orderable_aruba = st.session_state.backlog.copy()
                    # update the sidebar
                    placeholder3.success(' Successfuly uploaded aruba ', icon='✔️')
                    computeAruba(st.session_state.backlog, st.session_state.aruba, st.session_state.orderable_aruba)
                else:
                    placeholder3.error(' Please upload a file', icon='❌')

            # check if aruba is defined
            if 'aruba' in st.session_state:
                placeholder3.success(' Successfuly uploaded aruba ', icon='✔️')

        # select view
        view = st.selectbox('Select View', ['Data overview', 'Hit bundles', 'Sales'])
        # on selection of view
        if view == 'Data overview':
            dataOverview(st.session_state.backlog)
        elif view == 'Hit bundles':
            hitBundles(st.session_state.backlog, st.session_state.hitbundles, st.session_state.orderable)
        elif view == 'Sales':
            sales(st.session_state.backlog, st.session_state.orderable)

        
    