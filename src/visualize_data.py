import datetime
import pandas as pd
import plotly.graph_objects as go


def avg_data_day(boulderdf: pd.DataFrame, day: int, gym: str) -> pd.DataFrame:
    '''
    Input: dataframe with all data, weekday (0: Monday, 6: Sunday), gym name
    Output: dataframe with average data for the given input parameters
    '''
    
    # obtain only the data for the specific weekday and gym
    boulderdf['current_time'] = pd.to_datetime(boulderdf['current_time'])
    boulderdf = boulderdf[boulderdf.current_time.dt.weekday==day]
    boulderdf = boulderdf[boulderdf['gym_name'] == gym]

    # transform date to hour and minute format
    boulderdf['current_time'] = boulderdf['current_time'].dt.strftime('%H:%M')
    boulderdf.drop(['gym_name'], inplace=True, axis=1)

    # iterate through the hours and obtain the means for all values
    avgdf = []
    for t in boulderdf['current_time'].unique():
        for_time = boulderdf[boulderdf['current_time'] == t]
        avgdf.append([
            t,
            round(for_time['occupancy'].mean(), 2),
            int(for_time['waiting'].mean()),
            int(for_time['weather_temp'].mean()),
            for_time['weather_status'].max()
        ])

    avgdf = pd.DataFrame(data=avgdf, columns=['current_time', 'occupancy', 'waiting', 'weather_temp', 'weather_status'])
    avgdf.sort_values(by=['current_time'], inplace=True)
    return avgdf


def given_day(boulderdf: pd.DataFrame, selected_date: str, gym: str) -> pd.DataFrame:
    '''
    Input: dataframe with all data, a specific date, gym name
    Output: dataframe with all of the data for the given input parameters
    '''
    # make conversion from streamlit-type datetime to format in df
    selected_date = selected_date.replace('-', '/')
    # obtain only the data for the specific weekday and gym
    boulderdf = boulderdf[boulderdf['current_time'].str.contains(selected_date)]
    boulderdf = boulderdf[boulderdf['gym_name'] == gym]

    # transform date to hour and minute format
    boulderdf['current_time'] = boulderdf['current_time'].apply(lambda x: x.split()[1])
    boulderdf.drop(['gym_name'], axis=1, inplace=True)

    # sort the data by time
    boulderdf.sort_values(by=['current_time'], inplace=True)
    return boulderdf


def plot_data(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    # dash options include 'dash', 'dot', and 'dashdot
    fig.add_trace(go.Scatter(x=df.current_time, y=df.occupancy, name='Occupancy', line=dict(color='firebrick', width=4)))
    fig.add_trace(go.Scatter(x=df.current_time, y=df.waiting, name='Queue', line=dict(color='royalblue', width=4, dash='dash')))
    fig.add_trace(go.Scatter(x=df.current_time, y=df.weather_temp, name='Weather Temp', line = dict(color='green', width=4, dash='dot')))
    fig.update_layout(title='Plotting occupancy, queue and weather', xaxis_title='Time')

    fig['layout']['yaxis'].update(title='', range=[-5, 105], autorange=False)
    return fig
