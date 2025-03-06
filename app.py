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
data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y')

# Get the current date and calculate the date ranges for last month and the last 3 months
today = datetime.today()
last_month_start = today.replace(day=1) - timedelta(days=1)
last_3_months_start = today - timedelta(days=90)

# Filter the data for the required date ranges
data_last_month = data[data['Date'] >= last_month_start]
data_last_3_months = data[data['Date'] >= last_3_months_start]

# Calculate percentages for different statuses (Inbound, Dialogue, Accepted, Declined)
def calculate_percentages(df):
    total_projects = len(df)
    inbound_percentage = (df['Inbound'].notna().sum() / total_projects) * 100
    dialogue_percentage = (df['Dialogue'].notna().sum() / total_projects) * 100
    accepted_percentage = (df['Accepted'].notna().sum() / total_projects) * 100
    declined_percentage = (df['Declined'].notna().sum() / total_projects) * 100
    
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
    "Status": ["Inbound", "Dialogue", "Accepted", "Declined"],
    "Last Month": [last_month_percentages["Inbound"], last_month_percentages["Dialogue"], last_month_percentages["Accepted"], last_month_percentages["Declined"]],
    "Last 3 Months": [last_3_months_percentages["Inbound"], last_3_months_percentages["Dialogue"], last_3_months_percentages["Accepted"], last_3_months_percentages["Declined"]],
    "Overall": [overall_percentages["Inbound"], overall_percentages["Dialogue"], overall_percentages["Accepted"], overall_percentages["Declined"]]
})

# Plot the bar chart
fig = px.bar(percentages_data, 
             x="Status", 
             y=["Last Month", "Last 3 Months", "Overall"],
             title="Project Status Percentages",
             labels={"value": "Percentage", "variable": "Time Period"},
             color="variable",
             color_discrete_map={
                 "Last Month": "lightblue", 
                 "Last 3 Months": "blue", 
                 "Overall": "green"
             })

fig.update_layout(barmode='group', xaxis_title="Status", yaxis_title="Percentage (%)")

# Show the chart in Streamlit
st.plotly_chart(fig)
