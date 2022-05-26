import streamlit as st
import json 
import datetime

# Read the basic information from dictionary
with open('../dictionaries/master_dict.json') as json_file:
    master_dict = json.load(json_file)

start_date_input = datetime.datetime.now()

def show():
    with st.sidebar.header('User Inputs'):
        form = st.form(key='my_form')
        start_day = form.date_input("Select the date.", 
                                  start_date_input,
                                  min_value=datetime.date(2019, 1, 1), 
                                  max_value = start_date_input, 
                                  key = 'start_day')
        duration = form.slider('Select the duration based on the selected date.', 1, 100, 20,  key='duration')
        submit_button = form.form_submit_button(label='Submit')
        
        inputs = {
                  'duration' : duration,
                  'start_day' : start_day
        }

    
        return inputs

        
if __name__ == "__main__":
    show()