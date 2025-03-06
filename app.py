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
    total_projects = len(df)
    
    # Count the number of projects for each status
    inbound_count = (df['Inbound'] == "Yes").sum()
    dialogue_count = (df['Dialogue'] == "Yes").sum()
    accepted_count = (df['Accepted'] == "Yes").sum()
    declined_count = (df['Declined'] == "Yes").sum()

    # Calculate percentages
    inbound_percentage = (inbound_count / total_projects) * 100.0
    dialogue_percentage = (dialogue_count / total_projects) * 100.0
    accepted_percentage = (accepted_count / total_projects) * 100.0
    declined_percentage = (declined_count / total_projects) * 100.0
    
    return {
        "Inbound": inbound_percentage,
        "Dialogue": dialogue_percentage,
        "Accepted": accepted_percentage,
        "Declined": declined_percentage
    }

# Create data for plotting
last_month_percentages = calculate_percentages(data_last_month)
last_3_months_percentages = calculate_percentages(data_last_3_months)
overall_percentages = calculate_percentages(data)

# Create a DataFrame for easy plotting
percentages_data = pd.DataFrame({
    "Time Period": ["Last 30 Days", "Last 3 Months", "Overall"],
    "Inbound": [last_month_percentages["Inbound"], last_3_months_percentages["Inbound"], overall_percentages["Inbound"]],
    "Dialogue": [last_month_percentages["Dialogue"], last_3_months_percentages["Dialogue"], overall_percentages["Dialogue"]],
    "Accepted": [last_month_percentages["Accepted"], last_3_months_percentages["Accepted"], overall_percentages["Accepted"]],
    "Declined": [last_month_percentages["Declined"], last_3_months_percentages["Declined"], overall_percentages["Declined"]]
})

# Reshape the data for easier plotting (long format)
percentages_data_long = percentages_data.melt(id_vars="Time Period", var_name="Status", value_name="Percentage")

# Plot the bar chart
fig = px.bar(percentages_data_long, 
             x="Time Period", 
             y="Percentage", 
             color="Status", 
             title="Project success",
             labels={"Percentage": "Percentage (%)", "Time Period": "Time Period", "Status": "Project Status"},
             color_discrete_map={
                 "Inbound": "lightblue", 
                 "Dialogue": "blue", 
                 "Accepted": "green", 
                 "Declined": "red"
             })

fig.update_layout(barmode='group', xaxis_title="Time Period", yaxis_title="Percentage (%)")

# Show the chart in Streamlit
st.plotly_chart(fig)

### Chart 2: Application output

# Count the number of projects for each time frame
total_last_30_days = len(data_last_month)
total_last_90_days = len(data_last_3_months) / 3
first_job_ad_date = datetime(2024, 3, 7)
days_difference = (today - first_job_ad_date).days
months_difference = days_difference / 30
total_all_time = len(data) / months_difference

# Create a DataFrame for the total counts
total_counts = pd.DataFrame({
    'Time Frame': [ 'Last 30 Days', 'Last 90 Days', 'All Time'],
    'Applied Projects': [total_last_30_days, total_last_90_days, total_all_time]
})

# Plot the bar chart
fig = px.bar(total_counts, x='Time Frame', y='Applied Projects', title='Applied Projects per Month')
st.plotly_chart(fig)

### Chart 3: Attribution

# Count the number of applications per platform for each time frame
platform_attribution_all_time = data['Platform'].value_counts()
platform_attribution_last_month = data_last_month['Platform'].value_counts()
platform_attribution_last_3_months = data_last_3_months['Platform'].value_counts()

# Create a DataFrame to hold the counts for each time frame
platform_attribution_data = pd.DataFrame({
    'Platform': platform_attribution_all_time.index,
    'All Time': platform_attribution_all_time.values,
    'Last 30 Days': platform_attribution_last_month.values,
    'Last 90 Days': platform_attribution_last_3_months.values
}).fillna(0)

# Create a long-format DataFrame for Plotly (to plot stacked bar chart)
platform_attribution_long = platform_attribution_data.melt(id_vars='Platform', 
                                                           value_vars=['Last 30 Days', 'Last 90 Days', 'All Time'], 
                                                           var_name='Time Period', 
                                                           value_name='Number of Applications')

# Plot the stacked bar chart with Plotly
fig = px.bar(platform_attribution_long, 
             x='Time Period', 
             y='Number of Applications', 
             color='Platform',
             title='Platform Attribution by Time Range',
             color_discrete_map={
                 'Upwork': '#ff9999', 
                 'LinkedIn': '#66b3ff', 
                 'Project': '#99ff99', 
                 'Uplink': '#ffcc99'
             })

# Customize the layout for better readability
fig.update_layout(
    xaxis_title='Time Period',
    yaxis_title='Number of Applications',
    barmode='stack',
    title='Platform Attribution by Time Range'
)

# Show the chart in Streamlit
st.plotly_chart(fig)
