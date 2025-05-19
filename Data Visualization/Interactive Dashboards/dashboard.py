import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

#Load datasets
mobile_df = pd.read_csv('mobile_addiction_cleaned (1).csv')
behavior_df = pd.read_csv('user_behavior_dataset (2).csv')

#Text style
title_style_main = {
    'textAlign': 'center',
    'fontFamily': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
    'color': '#2C3E50',
    'fontWeight': 'bold',
    'fontSize': '36px',
    'marginBottom': '30px',
    'marginTop': '20px'
}

title_style_section = {
    'fontFamily': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
    'color': '#34495E',
    'fontWeight': 'bold',
    'fontSize': '24px',
    'marginTop': '30px',
    'marginBottom': '15px',
}

#Group ages into 5-year intervals for User Behavior
age_bins = list(range(int(behavior_df['Age'].min() // 5 * 5), int(behavior_df['Age'].max()) + 5, 5))
age_labels = [f"{age_bins[i]}–{age_bins[i + 1] - 1}" for i in range(len(age_bins) - 1)]
behavior_df['Age_Group'] = pd.cut(behavior_df['Age'], bins=age_bins, labels=age_labels, right=False)

#Group ages into 5-year intervals for Mobile Addiction
age_bins_mobile = list(range(int(mobile_df['age'].min() // 5 * 5), int(mobile_df['age'].max()) + 5, 5))
age_labels_mobile = [f"{age_bins_mobile[i]}–{age_bins_mobile[i + 1] - 1}" for i in range(len(age_bins_mobile) - 1)]
mobile_df['Age_Group'] = pd.cut(mobile_df['age'], bins=age_bins_mobile, labels=age_labels_mobile, right=False)

#Initialize app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Mobile Usage Dashboard"

#Layout
app.layout = html.Div([
    html.H1("Interactive Mobile Usage Dashboard", style=title_style_main),
    dcc.Tabs([
        #Mobile Addiction Tab
        dcc.Tab(label='Mobile Addiction',style=title_style_section,children=[
            html.Div([
                html.Label("Select Age Group (5-year intervals):", style=title_style_section),
                dcc.Dropdown(
                    id='age-dropdown-ma',
                    options=[{'label': group, 'value': group} for group in mobile_df['Age_Group'].cat.categories],
                    multi=True,
                    value=list(mobile_df['Age_Group'].cat.categories)
                ),

                html.H3("Notifications vs. Stress Level", style=title_style_section),
                dcc.Graph(id='ma-scatter-notification-stress'),

                html.H3("Average Social Media Usage by Addiction Status", style=title_style_section),
                dcc.Graph(id='ma-bar-socialmedia-addiction'),

                html.H3("Daily Screen Time vs. Stress Level", style=title_style_section),
                dcc.Graph(id='ma-scatter-screentime-stress')
            ])
        ]),

        #User Behavior Tab
        dcc.Tab(label='User Behavior', style=title_style_section, children=[
            html.Div([
                html.Label("Select Age Group (5-year intervals):", style=title_style_section),
                dcc.Dropdown(
                    id='age-dropdown-ub',
                    options=[{'label': group, 'value': group} for group in behavior_df['Age_Group'].cat.categories],
                    multi=True,
                    value=list(behavior_df['Age_Group'].cat.categories)
                ),

                html.Label("Select Gender:"),
                dcc.Dropdown(
                    id='gender-dropdown-ub',
                    options=[{'label': g, 'value': g} for g in behavior_df['Gender'].unique()],
                    multi=True,
                    value=behavior_df['Gender'].unique().tolist()
                ),
                html.H3("Average App Usage vs screen time", style=title_style_section),
                dcc.Graph(id='ub-graph'),

                html.H3("Average App Usage Time by Age Group", style=title_style_section),
                dcc.Graph(id='app-usage-bar'),

                html.H3("Average Feature Values by Behavior Class", style=title_style_section),
                dcc.Graph(id='behavior-class-bar')
            ])
        ])
    ])
])

#Callback for User Behavior main graph
@app.callback(
    Output('ub-graph', 'figure'),
    Input('age-dropdown-ub', 'value'),
    Input('gender-dropdown-ub', 'value')
)
def update_user_behavior(selected_age_groups, selected_genders):
    filtered_df = behavior_df.copy()

    if selected_age_groups:
        filtered_df = filtered_df[filtered_df['Age_Group'].isin(selected_age_groups)]

    if selected_genders:
        filtered_df = filtered_df[filtered_df['Gender'].isin(selected_genders)]

    fig = px.scatter(
        filtered_df,
        x='App_Usage_Time',
        y='Screen_On_Time',
        color='Age_Group',
    )
    return fig

#Callback for App Usage Time by Age Group
@app.callback(
    Output('app-usage-bar', 'figure'),
    Input('age-dropdown-ub', 'value')
)
def update_app_usage_bar(selected_age_groups):
    filtered_df = behavior_df.copy()
    if selected_age_groups:
        filtered_df = filtered_df[filtered_df['Age_Group'].isin(selected_age_groups)]

    grouped = filtered_df.groupby('Age_Group', as_index=False)['App_Usage_Time'].mean()

    fig = px.bar(
        grouped,
        x='Age_Group',
        y='App_Usage_Time',
        labels={'App_Usage_Time': 'Avg. App Usage Time (mins)', 'Age_Group': 'Age Group'},
        color='Age_Group'
    )
    return fig

#Callback for Behavior Class Feature Bar Chart
@app.callback(
    Output('behavior-class-bar', 'figure'),
    Input('age-dropdown-ub', 'value'),
)
def update_behavior_class_bar(selected_age_groups):
    filtered_df = behavior_df.copy()
    if selected_age_groups:
        filtered_df = filtered_df[filtered_df['Age_Group'].isin(selected_age_groups)]

    grouped = filtered_df.groupby('User_Behavior_Class')[['App_Usage_Time', 'Data_Usage', 'Battery_Drain']].mean().reset_index()

    melted = grouped.melt(
        id_vars='User_Behavior_Class',
        value_vars=['App_Usage_Time', 'Data_Usage', 'Battery_Drain'],
        var_name='Feature',
        value_name='Average Value'
    )

    fig = px.bar(
        melted,
        x='User_Behavior_Class',
        y='Average Value',
        color='Feature',
        barmode='group',
    )
    return fig

#Scatter Plot for Notifications vs. Stress Level
@app.callback(
    Output('ma-scatter-notification-stress', 'figure'),
    Input('age-dropdown-ma', 'value')
)
def update_notification_vs_stress(selected_age_groups):
    filtered_df = mobile_df[mobile_df['Age_Group'].isin(selected_age_groups)]
    filtered_df = filtered_df.dropna(subset=['notifications', 'stress_level'])

    fig = px.scatter(
        filtered_df,
        x='notifications',
        y='stress_level',
        color='Age_Group',
        labels={'notifications': 'Notifications', 'stress_level': 'Stress Level'},
    )
    return fig

#Bar Plot for Average Social Media Usage by Addiction Status
@app.callback(
    Output('ma-bar-socialmedia-addiction', 'figure'),
    Input('age-dropdown-ma', 'value')
)
def update_avg_socialmedia_addiction(selected_age_groups):
    filtered_df = mobile_df[mobile_df['Age_Group'].isin(selected_age_groups)]
    filtered_df = filtered_df.dropna(subset=['social_media_usage', 'addicted'])

    grouped = filtered_df.groupby('addicted', as_index=False)['social_media_usage'].mean()

    fig = px.bar(
        grouped,
        x='addicted',
        y='social_media_usage',
        color='addicted',
        labels={'social_media_usage': 'Avg. Social Media Usage (mins)', 'addicted': 'Addiction Status'},
    )
    return fig

#Scatter Plot for Daily Screen Time vs. Stress Level
@app.callback(
    Output('ma-scatter-screentime-stress', 'figure'),
    Input('age-dropdown-ma', 'value')
)
def update_screentime_vs_stress(selected_age_groups):
    filtered_df = mobile_df[mobile_df['Age_Group'].isin(selected_age_groups)]
    filtered_df = filtered_df.dropna(subset=['daily_screen_time', 'stress_level'])

    fig = px.scatter(
        filtered_df,
        x='daily_screen_time',
        y='stress_level',
        color='Age_Group',
        labels={'daily_screen_time': 'Daily Screen Time (hrs)', 'stress_level': 'Stress Level'},

    )
    return fig

if __name__ == '__main__':
    app.run(debug=True)