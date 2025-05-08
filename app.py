import streamlit as st  
import pandas as pd  
import plotly.express as px  
import gspread  
from oauth2client.service_account import ServiceAccountCredentials  
import json  
import os  
from datetime import datetime, timedelta

# Google Sheets authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

if os.path.exists("credentials.json"):
    # Local credentials
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
else:
    # Streamlit secrets
    credentials_dict = dict(st.secrets["google_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(json.dumps(credentials_dict)), scope)

# Authorize with Google Sheets
client = gspread.authorize(creds)
sheet = client.open("job-offers").worksheet("projects")
data = pd.DataFrame(sheet.get_all_records())  

#########################################################################
############################# Charting area #############################
#########################################################################

### Chart 1: Response

data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y')

# Get the current date and calculate the date ranges for last month and the last 3 months
today = datetime.today()
# Calculate the date ranges for the last 30 and last 90 days
last_30_days_start = today - timedelta(days=30)
last_90_days_start = today - timedelta(days=90)

# Filter the data for the last 30 and last 90 days
data_last_month = data[data['Date'] >= last_30_days_start]
data_last_3_months = data[data['Date'] >= last_90_days_start]

# Calculate percentages for different statuses (Inbound, Dialogue, Accepted, Declined) relative to the total applications
def calculate_percentages(df):
    
    # Count the number of projects for each status
    inbound_count = (df['Inbound'] == "Yes").sum()
    dialogue_count = (df['Dialogue'] == "Yes").sum()
    accepted_count = (df['Accepted'] == "Yes").sum()

    # Calculate percentages
    inbound_percentage = (inbound_count / len(df)) * 100.0
    dialogue_percentage = (dialogue_count / len(df)) * 100.0
    accepted_percentage = (accepted_count / len(df)) * 100.0
    
    return {
        "Inbound": inbound_percentage,
        "Dialogue": dialogue_percentage,
        "Accepted": accepted_percentage,
    }

# Create data for plotting
last_month_percentages = calculate_percentages(data_last_month)
last_3_months_percentages = calculate_percentages(data_last_3_months)
overall_percentages = calculate_percentages(data)

# Create a DataFrame for easy plotting
percentages_data = pd.DataFrame({
    "Status": ["Dialogue", "Inbound", "Accepted"],
    "Last 30 Days": [last_month_percentages["Dialogue"], last_month_percentages["Inbound"], last_month_percentages["Accepted"]],
    "Last 3 Months": [last_3_months_percentages["Dialogue"], last_3_months_percentages["Inbound"], last_3_months_percentages["Accepted"]],
    "Overall": [overall_percentages["Dialogue"], overall_percentages["Inbound"], overall_percentages["Accepted"]],
})

# Reshape the data for easier plotting (long format)
percentages_data_long = percentages_data.melt(id_vars="Status", var_name="Time Period", value_name="Percentage")

# Plot the bar chart
fig = px.bar(percentages_data_long, 
             x="Status", 
             y="Percentage", 
             color="Time Period", 
             title="Pipeline Status",
             labels={"Percentage": "Percentage (%)",  "Status": "Project Status", "Time Period": "Time Period"},
             color_discrete_map={
                 "Last 30 Days": "#c4b5fd", # indigo-200 
                 "Last 3 Months": "#818cf8", # indigo-400
                 "Overall": "#4f46e5", # indigo-600
             },
             text_auto='.0f')

fig.update_layout(barmode='group', xaxis_title="Status", yaxis_title="Percentage (%)")

# Show the chart in Streamlit
st.plotly_chart(fig)

### Chart 2: Application output
first_job_ad_date = datetime(2024, 3, 7)
months_difference = (today - first_job_ad_date).days / 30

total_counts = pd.DataFrame({
    'Time Frame': ['Last 30 Days', 'Last 90 Days', 'All Time'],
    'Applied Projects': [
        len(data_last_month),
        len(data_last_3_months) / 3,
        len(data) / months_difference
    ]
})

fig = px.line(total_counts, x='Time Frame', y='Applied Projects', title='Applied Projects per Month', color_discrete_sequence=["#818cf8"] ) # indigo-400
fig.update_yaxes(rangemode='tozero')
st.plotly_chart(fig)

### Chart 3: Attribution

# Count the number of applications per platform for each time frame
platform_attribution_all_time = data['Platform'].value_counts()
platform_attribution_last_month = data_last_month['Platform'].value_counts()
platform_attribution_last_3_months = data_last_3_months['Platform'].value_counts()

# Calculate total applications for each time frame
total_all_time = platform_attribution_all_time.sum()
total_last_month = platform_attribution_last_month.sum()
total_last_3_months = platform_attribution_last_3_months.sum()

# Create a DataFrame to hold the counts for each time frame, then convert counts to percentages
platform_attribution_data = pd.DataFrame({
    'platform': platform_attribution_all_time.index,
    'all time': (platform_attribution_all_time.values / total_all_time) * 100,
    'last 30 days': (platform_attribution_last_month.values / total_last_month) * 100,
    'last 90 days': (platform_attribution_last_3_months.values / total_last_3_months) * 100
}).fillna(0)

# create a long-format dataframe for plotly (to plot stacked bar chart)
platform_attribution_long = platform_attribution_data.melt(id_vars='platform', 
                                                           value_vars=['last 30 days', 'last 90 days', 'all time'], 
                                                           var_name='time period', 
                                                           value_name='percentage of applications')

# Plot the stacked bar chart with Plotly
fig = px.bar(platform_attribution_long, 
             x='time period', 
             y='percentage of applications', 
             color='platform',
             title='platform attribution',
             color_discrete_map={
                 'upwork': '#14a800', 
                 'linkedin': '#3463bd', 
                 'project': '#95c7fb', 
                 'uplink': '#e9664c'
             })

# Customize the layout for better readability
fig.update_layout(
    xaxis_title='Time Period',
    yaxis_title='Percentage of Applications',
    barmode='stack',
    title='Platform Attribution'
)

# Show the chart in Streamlit
st.plotly_chart(fig)
