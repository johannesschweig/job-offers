import streamlit as st  
import pandas as pd  
import plotly.express as px  
import plotly.graph_objects as go
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
fig = go.Figure(go.Indicator(
    mode = "number+delta",
    value = len(data_last_month),
    delta = {'position': "top", 'reference': round(len(data_last_3_months) / 3)},
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "Applied projects in the last 30 days<br><span style='font-size:0.8em;color:gray'>vs. in the last 3 months</span>"},
))

st.plotly_chart(fig)

### Chart 3: Attribution

# Calculate platform counts for each time frame
platform_counts_last_30_days = data_last_month['Platform'].value_counts()
platform_counts_last_3_months = data_last_3_months['Platform'].value_counts()
platform_counts_overall = data['Platform'].value_counts()

# Get the union of all platforms to ensure consistent indexing
all_platforms = set(platform_counts_last_30_days.index).union(
    platform_counts_last_3_months.index,
    platform_counts_overall.index
)

# Reindex the counts to include all platforms and fill missing values with 0
platform_counts_last_30_days = platform_counts_last_30_days.reindex(all_platforms, fill_value=0)
platform_counts_last_3_months = platform_counts_last_3_months.reindex(all_platforms, fill_value=0)
platform_counts_overall = platform_counts_overall.reindex(all_platforms, fill_value=0)

# Create the DataFrame
platform_attribution_data = pd.DataFrame({
    'Platform': list(all_platforms) * 3,
    'Time Frame': ['Last 30 Days'] * len(all_platforms) +
                  ['Last 3 Months'] * len(all_platforms) +
                  ['Overall'] * len(all_platforms),
    'Total': list(platform_counts_last_30_days.values) +
             list(platform_counts_last_3_months.values) +
             list(platform_counts_overall.values)
})

percentages = platform_attribution_data.groupby('Time Frame')['Total'].transform(
    lambda x: (x / x.sum()) * 100
)

platform_attribution_data['Percentage'] = percentages



# Define brand colors for the platforms
platform_colors = {
    "linkedin": "#0a66c2",  # LinkedIn blue
    "project": "#21cda4",   # freelancermap teal
    "slack": "#4a154b",     # Slack purple
    "uplink": "#e9664c",    # uplink orange
    "upwork": "#14a800",    # Upwork green
}

# Get the top 3 platforms for each time frame
top_3_platforms = platform_attribution_data.groupby('Time Frame').apply(
    lambda x: x.nlargest(3, 'Percentage')
).reset_index(drop=True)

time_frame_order = ["Last 30 Days", "Last 3 Months", "Overall"]

# Create a horizontal bar chart with Time Frame on the y-axis
fig = px.bar(
    top_3_platforms,
    x="Percentage",
    y="Time Frame",
    color="Platform",
    orientation="h",
    title="Top 3 Platforms",
    labels={"Percentage": "Percentage (%)", "Platform": "Platform", "Time Frame": "Time Frame"},
    color_discrete_map=platform_colors,
    text="Percentage",
    text_auto='.0f',
)

# Update layout for better readability
fig.update_layout(
    xaxis_title="Percentage (%)",
    yaxis_title="Time Frame",
    barmode="group",
    legend_title="Platform",
    yaxis=dict(categoryorder="array", categoryarray=time_frame_order)  # Custom order for Time Frame
)

# Show the chart in Streamlit
st.plotly_chart(fig)

