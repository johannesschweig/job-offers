import streamlit as st  
import pandas as pd  
import plotly.express as px  
import gspread  
from oauth2client.service_account import ServiceAccountCredentials  

#1CWb4l90bLRHTIOZ3J627B645ERc0eQms95OLv-K-cEI
# Connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("job-offers").worksheet("projects")

# Load data into a Pandas DataFrame  
data = pd.DataFrame(sheet.get_all_records())  

# Rename columns for easier access  
data.columns = ["No", "Job", "Date", "Inbound", "Dialogue", "Declined", "Accepted", "Date_US", "Platform", "Notes"]

# Count applications per platform  
platform_counts = data["Platform"].value_counts().reset_index()  
platform_counts.columns = ["Platform", "Applications"]  

# Streamlit App  
st.title("📊 Job Application Tracker")  

# Plotly Bar Chart (Platform Performance)  
fig = px.bar(platform_counts, x="Platform", y="Applications", color="Platform", title="Applications by Platform")
st.plotly_chart(fig)
