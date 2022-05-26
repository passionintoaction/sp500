import streamlit as st
import json 

# Read the basic information from dictionary
with open('../dictionaries/master_dict.json') as json_file:
    master_dict = json.load(json_file)
    
def show():
    with st.sidebar.header('User Inputs'):
        form = st.form(key='my_form')
        
        sector = form.multiselect('Sector', master_dict["sector"], key='sector')
        period = form.radio("Investment Period You Are Interested.",
                            (master_dict["period"][0], 
                             master_dict["period"][1], 
                             master_dict["period"][2]), 
                             key='period')
        risk = form.slider('Investment Risk You Can Take: Low(1) - High(3)', 
                                                        master_dict["risk"][0], 
                                                        master_dict["risk"][-1], 
                                                        key='risk')
        
        submit_button = form.form_submit_button(label='Submit')
        
        inputs = {
                  'sector' : sector, 
                  'risk' : risk,
                  'period' : period
        }

    
        return inputs

        
if __name__ == "__main__":
    show()