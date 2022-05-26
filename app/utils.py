import numpy as np
import os
import json
import io
import importlib.util
import collections
import pandas as pd
import altair as alt
from altair import * 


def load_model_templates():
    template_dict = collections.defaultdict(dict)
    template_dirs = [f for f in os.scandir("./UI_templates") if f.is_dir()]
    template_dirs = sorted(template_dirs, key=lambda e: e.name)
    
    for template_dir in template_dirs:
        try:
            model, task = template_dir.name.split("-")
            template_dict[model][task] = template_dir.path
            
        except ValueError:
            template_dict[template_dir.name] = template_dir.path
            
    return template_dict

def import_from_file(module_name: str, filepath: str):
    """
    import a module from file.
    Args:
        module name(str): Assigned to the module's __name__parameter (does not 
                          influence how the moule is named outside of this function)
        filepath(str): Path to the .py file
    Returns:
        the module
    """
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def pct_rank_qcut(series, n):
    edges = pd.Series([float(i) / n for i in range(n + 1)])
    f = lambda x: (edges >= x).values.argmax()
    return series.rank(pct=1).apply(f)

def get_chart(data):
    hover = alt.selection_single(
        fields=["Date"],
        nearest=True,
        on="mouseover",
        empty="none",
    )

    lines = (
        alt.Chart(data, title="Stock Prices")
        .mark_line()
        .encode(
            x="Date",
            y="Close",
            color="ticker",
            strokeDash= "ticker",
        )
    )

    # Draw points on the line, and highlight based on selection
    points = lines.transform_filter(hover).mark_circle(size=65)

    # Draw a rule at the location of the selection
    tooltips = (
        alt.Chart(data)
        .mark_rule()
        .encode(
            x="Date",
            y="Close",
            opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=[
                alt.Tooltip("Date", title="Date"),
                alt.Tooltip("Close", title="Price (USD)"),
            ],
        )
        .add_selection(hover)
    )

    return (lines + points + tooltips).interactive()


