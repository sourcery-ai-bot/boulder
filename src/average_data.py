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

    avgdf = pd.DataFrame(data=avgdf, columns=['time', 'occupancy', 'waiting', 'weather_temp', 'weather_status'])
    avgdf.sort_values(by=['time'], inplace=True)
    return avgdf


def plot_ave_data(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df.time, y=df.occupancy, name='Occupancy',
                         line=dict(color='firebrick', width=4)))
    fig.add_trace(go.Scatter(x=df.time, y=df.waiting, name='Waiting',
                         line=dict(color='royalblue', width=4,
                              dash='dash'))) # dash options include 'dash', 'dot', and 'dashdot
    fig.add_trace(go.Scatter(x=df.time, y=df.weather_temp, name='Weather Temp',
                         line = dict(color='green', width=4, dash='dot')))

    fig.update_layout(title='Plotting average occupancy, waiting people and weather',
                   xaxis_title='Time')

    fig['layout']['yaxis'].update(title='', range=[-5, 105], autorange=False)


    return fig