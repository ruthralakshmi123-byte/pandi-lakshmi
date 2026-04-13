# ER Command Center Dashboard

A real-time hospital operations dashboard built with Python and Streamlit.

This application simulates live patient arrivals every 60 seconds and displays emergency room occupancy, average wait times, critical triage alerts, department-wise patient load, and live weather impact by city.

## Features

- Real-time fake patient feed
- Auto-refreshing dashboard
- Current ER Occupancy KPI
- Average Wait Time KPI
- Critical Triage Patients alert
- Occupancy by Department chart
- Admissions Over Time chart
- Live Weather by City
- Weather Impact Summary
- Command center style hospital dashboard UI

## Tech Stack

- Python
- Streamlit
- Pandas
- Requests
- SQLite
- Open-Meteo Weather API

## Project Files

- `hospital_dashboard.py` - Main Streamlit hospital app
- `requirements.txt` - Required Python packages

## Installation

Install the required packages using:

```bash
python -m pip install -r requirements.txt
```

## Run the App

Start the dashboard with:

```bash
python -m streamlit run hospital_dashboard.py
```

## Live App Link

Deployed Streamlit App:  
PASTE_HOSPITAL_APP_LINK_HERE

## Dashboard Output

The dashboard displays:

- Current ER Occupancy
- Average Wait Time
- Critical Triage Patients
- Live Patient Feed
- Occupancy by Department
- Admissions Over Time
- Live Weather by City
- Weather Impact Summary

## Deployment Steps

1. Create a GitHub repository
2. Upload `hospital_dashboard.py` and `requirements.txt`
3. Open Streamlit Community Cloud
4. Click **Deploy an app**
5. Select repository, branch, and `hospital_dashboard.py`
6. Click **Deploy**
7. Share the generated app link

## Author

# pandi-lakshmi
