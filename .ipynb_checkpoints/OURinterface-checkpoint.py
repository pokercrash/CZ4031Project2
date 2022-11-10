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
    for x in impt_breakers:
        if len(text.split(x)) == 2:
            a, b = text.split(x)
            text = x + " " + b
            list_of_breakdown += [a.strip()]
    list_of_breakdown += [text]
    list1 = [x+1 for x in range(len(list_of_breakdown)-1)]
    return pd.DataFrame({"line": list1, "query": list_of_breakdown[1:]})


select_statement = "select * \n from customer C, orders O \n where C.c_custkey = O.o_custkey"
query_df = process_select(select_statement)

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
        return fig, process_select(text).to_dict('records'), 0


@callback(Output('tbl_out', 'children'), Input('tbl', 'active_cell'))
def update_graphs(active_cell):
    return "This join is implemented using hash join operator as NL joins and merge join increase the estimated cost by at least 10 and 7 times, respectively." if active_cell else "Click the table"


if __name__ == "__main__":
    app.run_server(debug=False, port=8051)
