######### main.py

import streamlit as st
import pandas as pd 
import numpy as np 
import os
import json
import utils
import api

# Read the basic information from dictionary
with open('./dictionaries/master_dict.json') as json_files:
    master_dict = json.load(json_files)
    
    
# Load main page template
template_main_page = utils.import_from_file("template_main", "./app/display_main_page.py")
# Load model templates
template_dict = utils.load_model_templates()
    
with st.sidebar:
    #st.write("## Menu")
    template_dict["Home"] = './UI_templates/Home/'
    model = st.selectbox("MENU", list(template_dict.keys()), index=1)
    
    if isinstance(template_dict[model], dict):
        task = st.selectbox("Select geographical level",list(template_dict[model].keys()), index=0 )
        template_dir = template_dict[model][task]
    
    else:
        template_dir = template_dict[model]
        task=''
        
# Show template-specific sidebar components (based on sidebar.py in the template dir) 
template_sidebar = utils.import_from_file("template_sidebar", os.path.join(template_dir, "sidebar.py"))
input_dict = template_sidebar.show()

# Show main pages 
with st.spinner("Retrieving Result Please Wiat..."):
    res=api.call_api(input_dict, model, task)
    
# Display main page components based on main page template
template_main_page.show(res, model, task, input_dict)
