import json
import tkinter as tk
from tkinter import font, ttk, messagebox
from typing import Text
import interface
from node_types import ATTRIBUTE
import sqlparse
import node_types
import psycopg2
import annotation
import newinterface
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, callback, dash_table
import pandas as pd
import plotly.express as px

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
df = pd.DataFrame({
    "Plan": ['1', '2', '3', '4'],
    "Amount": [4, 1, 2, 9]
})


impt_breakers = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY']

fig = px.bar(df, x="Plan", y="Amount", color="Amount", barmode="group")


def process_select(select_statement):
    text = select_statement.strip().upper()
    list_of_breakdown = []
    global cutting
    cutting = []
    oldlen = 0
    for x in impt_breakers:
        if len(text.split(x)) == 2:
            a, b = text.split(x)
            cutting += [len(a.strip())+oldlen]
            oldlen = len(a.strip())
            text = x + " " + b
            list_of_breakdown += [a.strip()]
    list_of_breakdown += [text]
    list1 = [x+1 for x in range(len(list_of_breakdown)-1)]

    return pd.DataFrame({"line": list1, "query": list_of_breakdown[1:]}), cutting


select_statement = "select * \n from customer C, orders O \n where C.c_custkey = O.o_custkey"
query_df, cutting = process_select(select_statement)

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "30rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "30rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H2("DBP Query \nOptimiser", className="display-4"),
        html.Hr(),
        html.P(
            "Input", className="lead"
        ),
        dcc.Textarea(
            id='textarea-example',
            placeholder='Input SQL Query here ...',
            style={'width': '100%', 'height': 300},
        ),
        html.Div(id='textarea-example-output',
                 style={'whiteSpace': 'pre-line'}),
        dbc.Button('Submit', id='submit-val', n_clicks=0)
    ],

    style=SIDEBAR_STYLE,
)

content = html.Div([
    dcc.Dropdown(['Choice A', 'Choice B'], 'Choice B', id='dropdown'),
    dcc.Graph(
        id='example-graph',
        figure=fig
    ), dbc.Label('Click a cell in the table:'),
    dash_table.DataTable(query_df.to_dict('records'), [
                         {"name": i, "id": i} for i in query_df.columns], id='tbl'),
    dbc.Alert(id='tbl_out')], style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

impt_breakers = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY']

list_of_annotations = []


@app.callback(
    Output('example-graph', 'figure'),
    Output('tbl', 'data'),
    Output('submit-val', 'n_clicks'),
    [Input('dropdown', 'value'),
     Input('textarea-example', 'value'),
     Input('submit-val', 'n_clicks')
     ])
def user_model(dropdown_value, text, submit_val):
    if submit_val != 0:
        newinterface.get_json(text)
        global list_of_annotations
        list_of_annotations = get_query_list(text)
        a, b = process_select(text)
        return fig, a.to_dict('records'), 0


def get_query_list(text):
    node_list = newinterface.execute_query(text)
    return node_list


def insert_into_dict1(dict1, k, v):
    if k not in dict1.keys():
        dict1[k] = [v]
    else:
        dict1[k] += [v]


def get_particular_keyword(node_list):
    dict1 = {}
    for x in node_list:
        flag = 0
        for y in range(0, len(cutting)):
            # print(x[-1],b[y])
            if int(x[-1]) < int(cutting[y]) and int(x[-1]) > int(cutting[y-1]):
                insert_into_dict1(dict1, y-1, x[0])
                flag = 1
                break
        if flag == 0:
            insert_into_dict1(dict1, y, x[0])
    return dict1


@callback(Output('tbl_out', 'children'), Input('tbl', 'active_cell'))
def update_graphs(active_cell):
    print(active_cell)
    dict1 = get_particular_keyword(list_of_annotations)
    if active_cell['row'] in dict1.keys():
        return dict1[active_cell['row']]
    else:
        return 'no data avail'


if __name__ == "__main__":
    app.run_server(debug=False, port=8051)

    # interface.get_json(retrieveInput(query_text))
    # interface.execute_query(root, retrieveInput())
