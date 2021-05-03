import requests
import json
from datetime import datetime
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

all_sessions = []

calendar_url = 'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id=%s&date=%s'
districts_url = 'https://cdn-api.co-vin.in/api/v2/admin/location/districts/%s'
states_url = 'https://cdn-api.co-vin.in/api/v2/admin/location/states'


def get_districts(state_id, state_name):
    districts_resp = requests.get(
        districts_url % state_id)

    districts = json.loads(
        districts_resp.content.decode("utf-8"))['districts']

    district_df = pd.DataFrame().from_records(districts)

    selected_districts = st.sidebar.multiselect(
        f'Districts for State:{state_name}', district_df['district_name'])
    district_df['state_name'] = state_name
    district_df['state_id'] = state_id
    return pd.DataFrame(district_df[district_df['district_name'].isin(selected_districts)])


def get_states():
    states = json.loads(requests.get(
        states_url).content.decode('utf-8'))['states']
    return states


def find_sessions(center, min_age=45):
    sessions = []
    for session in center['sessions']:
        if session['min_age_limit'] == min_age and session['available_capacity'] > 0:
            sessions += [{'date': session['date'],
                          'state_name': center['state_name'],
                          'district_name': center['district_name'],
                          'name': center['name'],
                          'pincode': center['pincode'],
                          'fee_type': center['fee_type'],
                          'from': center['from'],
                          'to': center['to'],
                          'available_capacity': session['available_capacity'],
                          'min_age_limit': session['min_age_limit'],
                          'vaccine': session['vaccine'],
                          }]
    return sessions


states = get_states()
states_df = pd.DataFrame().from_records(states)

st.title('Vaccine Availability')
st.sidebar.title('Select Options')
st.sidebar.button('Refresh')
age = st.sidebar.radio('Age Group', [18, 45])
selected_states = st.sidebar.multiselect(
    'Select State', [state['state_name'] for state in states])

state_ids = states_df[states_df['state_name'].isin(
    selected_states)].values

selected_districts = []
for state_id, state_name in state_ids:
    selected_districts += [get_districts(state_id, state_name)]

selected_districts_df = pd.DataFrame()
if selected_districts:
    selected_districts_df = pd.concat(selected_districts)

weeks = st.sidebar.slider('Number of Weeks', min_value=1, max_value=10)

if not selected_districts_df.empty:
    for i in range(weeks):
        date_str = (datetime.today() + timedelta(days=7*i)
                    ).strftime('%d-%m-%Y')
        for district_id in selected_districts_df['district_id']:
            calendar_resp = requests.get(
                calendar_url % (district_id, date_str))
            calendar = json.loads(calendar_resp.content.decode('utf-8'))
            for center in calendar['centers'][:]:
                all_sessions += find_sessions(center, age)

sessions_df = pd.DataFrame().from_records(all_sessions)

centers_df = pd.DataFrame()
vaccine_counts_df = pd.DataFrame()
vaccine_centers_df = pd.DataFrame()

if not sessions_df.empty:
    centers_df = sessions_df.groupby(
        'state_name').size().to_frame('center_counts').reset_index()
    vaccine_counts_df = sessions_df.groupby(
        'state_name').agg({'available_capacity': 'sum'}).reset_index()
    vaccine_centers_df = sessions_df.sort_values(
        ['date', 'available_capacity', 'name'], ascending=[True, False, True]).reset_index()


st.subheader('Center Count By States')
st.table(centers_df)
st.subheader('Vaccine Count By States')
st.table(vaccine_counts_df)
st.subheader('Centers')
st.table(vaccine_centers_df)
