import json
import annotation
import interface
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, callback, dash_table
import pandas as pd
import plotly.express as px
import graphviz
from anytree import PreOrderIter
import dash_interactive_graphviz


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
df = pd.DataFrame({
    "FILLER GRAPH - SELECT DROPDOWN": ['1', '2', '3', '4'],
    "Amount": [4, 1, 2, 9]
})


impt_breakers = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY']

fig = px.bar(df, x="FILLER GRAPH - SELECT DROPDOWN", y="Amount", color="Amount",
             barmode="group", text_auto=True)


def get_dot_plot(query):
    json1 = interface.get_json(query)
    dict1 = json.loads(json1[3:-3])
    parents = []

    root_node = annotation.build_tree([dict1['Plan']])[0]
    graphviz.set_jupyter_format('png')
    dot = graphviz.Digraph(comment='The Round Table')
    # dot.node('GATHER')
    list_con = []
    list1 = []
    parents = []
    for node in PreOrderIter(root_node):
        parents += [type(node.parent)]

    for node in PreOrderIter(root_node):
        if type(node.parent) != parents[0]:
            print(node.id, node.parent.id)
            if node.id in list1:
                list_con += [[node.parent.id, node.id +
                              " " + str(list1.count(node.id))]]
                list1 += [node.id + " " + str(list1.count(node.id))]
            else:
                list_con += [[node.parent.id, node.id]]
                list1 += [node.id]
        else:
            dot.node(node.id)

    # for x in list1:
    #     dot.node(x[1])
    list_con = list_con[::-1]
    for x in list_con:
        dot.edge(x[0], x[1])

    return dot.source


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

GRAPH_STYLE = {
    "width": "50%",
    "height": "50%",
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
        dbc.Button('Submit', id='submit-val', n_clicks=0),
        html.Br(),
        html.H4('Note: Loading takes a few minutes', id='loading')
    ],

    style=SIDEBAR_STYLE,
)

content = html.Div([
    dcc.Dropdown(['Scan Bar Graph', 'Loop Bar Graph'],
                 'Loop Bar Graph', id='dropdown'),
    dcc.Graph(
        id='example-graph',
        figure=fig
    ), dbc.Label('Click a cell in the table:'),
    dash_table.DataTable(query_df.to_dict('records'), [
                         {"name": i, "id": i} for i in query_df.columns], id='tbl'),
    dbc.Alert(id='tbl_out'),
    dash_interactive_graphviz.DashInteractiveGraphviz(
        id="graph", style=GRAPH_STYLE)

], style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

impt_breakers = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY']

list_of_annotations = []


# @app.callback(
#     Output('example-graph', 'figure'),
#     Output('graph', 'dot_source'),
#     Output('tbl', 'data'),
#     Output('submit-val', 'n_clicks'),
#     [Input('dropdown', 'value'),
#      Input('textarea-example', 'value'),
#      Input('submit-val', 'n_clicks')
#      ])
# def user_model(dropdown_value, text, submit_val):
#     if submit_val != 0:
#         # interface.get_json(text)
#         global list_of_annotations, df_scan, df_loop
#         list_of_annotations, df_scan, df_loop = get_query_list(text)
#         a, b = process_select(text)
#         dot_source = get_dot_plot(text)
#         if dropdown_value == 'Scan Bar Graph':
#             df = df_scan.transpose().reset_index()
#             name = list(df.columns)[1]
#             df = df.rename(columns={name: 'amount'})
#             px.bar(df, x='index', y="amount")
#         else:
#             df = df_loop.transpose().reset_index()
#             name = list(df.columns)[1]
#             df = df.rename(columns={name: 'amount'})
#             df
#             fig = px.bar(df, x='index', y="amount")
#         return fig, dot_source, a.to_dict('records'), 0

@app.callback(
    # Output('example-graph', 'figure'),
    Output('graph', 'dot_source'),
    Output('tbl', 'data'),
    Output('submit-val', 'n_clicks'),
    [
        Input('textarea-example', 'value'),
        Input('submit-val', 'n_clicks')
    ])
def user_model(text, submit_val):
    if submit_val != 0:
        # interface.get_json(text)
        global list_of_annotations, df_scan, df_loop
        list_of_annotations, df_scan, df_loop = get_query_list(text)
        a, b = process_select(text)
        dot_source = get_dot_plot(text)
        print(df_loop)

        return dot_source, a.to_dict('records'), 0


@app.callback(
    Output('example-graph', 'figure'),
    Input('dropdown', 'value'))
def update_fig(dropdown_value):
    if dropdown_value == 'Scan Bar Graph':
        df = df_scan.transpose().reset_index()
        name = list(df.columns)[1]
        df = df.rename(columns={name: 'amount'})
        fig = px.bar(df, x='index', y="amount", text_auto=True)
    else:
        df = df_loop.transpose().reset_index()
        name = list(df.columns)[1]
        df = df.rename(columns={name: 'amount'})
        fig = px.bar(df, x='index', y="amount", text_auto=True)
    return fig


def get_query_list(text):
    node_list, scan_df, loop_df = interface.execute_query(text)
    return node_list, scan_df, loop_df


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
            if int(x[1]) < int(cutting[y]) and int(x[1]) > int(cutting[y-1]):
                insert_into_dict1(
                    dict1, y-1,  "\n{}:\n{}".format(
                        x[-1], x[0].strip().split("\n", 1)[-1]))
                flag = 1
                break
        if flag == 0:
            insert_into_dict1(dict1, y, "\n{}:\n{}".format(
                x[-1], x[0].strip().split("\n", 1)[-1]))
    print(dict1)
    return dict1


@ callback(Output('tbl_out', 'children'), Input('tbl', 'active_cell'))
def update_graphs(active_cell):
    print(active_cell)
    dict1 = get_particular_keyword(list_of_annotations)
    if active_cell['row'] in dict1.keys():
        return html.H5(dict1[active_cell['row']], style={'whiteSpace': 'pre-wrap'})


if __name__ == "__main__":
    app.run_server(debug=False, port=8051)
