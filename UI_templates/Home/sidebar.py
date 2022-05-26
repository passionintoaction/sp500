import streamlit as st
import json 

with open('./dictionaries/master_dict.json') as json_file:
    master_dict = json.load(json_file)

def show():
    with st.sidebar.header('User Inputs'):
        form = st.form(key='my_form')
#         submit_button = form.form_submit_button(label=Submit)
#         sector = form.selectbox('Sector', master_dict["sector"], key='sector')
# 14
        
# 15
#         inputs = {
# 16
#                   'sector' : sector
# 17
#         }
# 18

if __name__ == "__main__":
    show()
