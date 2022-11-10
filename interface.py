import json
import tkinter as tk
from tkinter import font, messagebox
from node_types import ATTRIBUTE
from anytree import PreOrderIter
import sqlparse
import node_types
import psycopg2
import annotation

def get_json(inputValue, permutations = ""):
        """ query parts from the parts table """
        
        conn = None
        x = None 
        try:
            #connect to postgres in this format
            conn = psycopg2.connect(
                host="localhost",
                database="TPC-H",
                user="postgres",
                password="password")
            
            cur = conn.cursor()
            cur.execute(permutations + "EXPLAIN (ANALYZE, VERBOSE, FORMAT JSON)" + inputValue)
            rows = cur.fetchall()
            x = json.dumps(rows)

            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            messagebox.showerror("Error",error)
            print(error)
        finally:
            if conn is not None:
                conn.close()
        print("success")
        return x

#function to connect to the PostgreSQL database
def connect():
        """ Connect to the PostgreSQL database server """
        conn = None
        try:
            # read connection parameters
            params = conn

            # connect to the PostgreSQL server
            print('Connecting to the PostgreSQL database...')
            conn = psycopg2.connect(**params)
            
            # create a cursor
            cur = conn.cursor()
            
        # execute a statement
            print('PostgreSQL database version:')
            cur.execute('SELECT version()')

            # display the PostgreSQL database server version
            db_version = cur.fetchone()
            print(db_version)
        
        # close the communication with the PostgreSQL
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
                print('Database connection closed.')
        cur = conn.cursor()

#14 colors for the 14 different node types
COLORS = [
    ('#ff6459', 'black'),
    ('#e91e63', 'black'),
    ('#9c27b0', 'white'),
    ('#673ab7', 'white'),
    ('#3f51b5', 'black'),
    ('#2196f3', 'black'),
    ('#03a9f4', 'black'),
    ('#00bcd4', 'black'),
    ('#009688', 'black'),
    ('#47d34d', 'black'),
    ('#8bc34a', 'black'),
    ('#cddc39', 'black'),
    ('#ffeb3b', 'black'),
    ('#ffc107', 'black')
]

NODE_COLORS = {node_type: color
            for node_type, color in zip(node_types.NODE_TYPES, COLORS)}

#GUI for displaying the tree 
class TreeFrame(tk.Frame):
    def __init__(self, root):
        tk.Frame.__init__(self, root)
        self.button_font = font.Font(family='Google Sans Display', size=12, weight='bold')
        self.label_font = font.Font(family='Google Sans Display', size=10)
        self.canvas = tk.Canvas(self, background= '#c5ded2')
        self.canvas.grid(row=0, column=1)

        #label
        # self.query_label = tk.Label(self, text='Click on the\n node to view \n analysis!', font = self.label_font, bg='#c5ded2')
        # self.query_label.grid(sticky=tk.N+ tk.W, row=0, column = 1, padx=12, pady=(12, 0))
        
        self._on_hover_listener = None
        self._on_click_listener = None
        self._on_hover_end_listener = None

    def draw_tree(self, root_node):
        bbox = self._draw_node(root_node, 12, 12)
        self.canvas.configure(width=bbox[2] - bbox[0] + 24, height=bbox[3] - bbox[1] + 24)

    def set_on_hover_listener(self, on_hover_listener):
        self._on_hover_listener = on_hover_listener

    def set_on_click_listener(self, on_click_listener):
        self._on_click_listener = on_click_listener

    def set_on_hover_end_listener(self, on_hover_end_listener):
        self._on_hover_end_listener = on_hover_end_listener

    def _on_click(self, node):
        if self._on_click_listener is not None:
            self._on_click_listener(node)

    def _on_hover(self, node):
        if self._on_hover_listener is not None:
            self._on_hover_listener(node)

    def _on_hover_end(self, node):
        if self._on_hover_end_listener is not None:
            self._on_hover_end_listener(node)

    def _draw_node(self, node, x1, y1):
        child_x = x1
        left = x1
        right = -1
        top = y1
        bottom = -1
        button = tk.Button(self.canvas, text=node.node_type, padx=12,
                        bg='#7d8ed1', fg='white', font=self.button_font, anchor='center')
        button.bind('<Button-1>', lambda event: self._on_click(node))
        button.bind('<Enter>', lambda event: self._on_hover(node))
        button.bind('<Leave>', lambda event: self._on_hover_end(node))
        window = self.canvas.create_window((x1, y1), window=button, anchor='nw')
        bbox = self.canvas.bbox(window)
        child_bboxes = []
        if len(node.children) == 0:
            return bbox
        for child in node.children:
            child_bbox = self._draw_node(child, child_x, y1 + 60)  # (x1, y1, x2, y2)
            child_x = child_bbox[2] + 20
            right = max(right, child_bbox[2])
            bottom = max(bottom, child_bbox[3])
            child_bboxes.append(child_bbox)
        x_mid = (left + right) // 2
        bbox_mid_x = (bbox[0] + bbox[2]) // 2
        self.canvas.move(window, x_mid - bbox_mid_x, 0)
        for child_bbox in child_bboxes:
            child_mid_x = (child_bbox[0] + child_bbox[2]) // 2
            self.canvas.create_line(x_mid, bbox[3], child_mid_x, child_bbox[1], width=2, arrow=tk.FIRST)
        return left, top, right, bottom

#GUI for displaying the input query on the second page
class QueryFrame(tk.Frame):
    def __init__(self, root):
        tk.Frame.__init__(self, root)
        self.text_font = font.Font(family='Fira Code Retina', size=12)
        self.text = tk.Text(self, height=18, font=self.text_font)
        self.text.grid(row=0, column=0)
        self.scrollbar = tk.Scrollbar(self, orient='vertical', command=self.text.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.text.configure(yscrollcommand=self.scrollbar.set)

        for node_type, color in NODE_COLORS.items():
            self.text.tag_configure(node_type, background=color[0], foreground=color[1])
        self.text.tag_configure('OTHER', background='#ff9800', foreground='black')

        self.index_map = {}
        self.query = None

    def set_query(self, query):
        self.query = query
        self.text.delete('1.0', 'end')
        self.text.insert('end', query)

        self.index_map = {}
        line = 1
        column = 0
        index = 0
        while index <= len(query):
            self.index_map[index] = f'{line}.{column}'
            if index < len(query) and query[index] == '\n':
                line += 1
                column = 0
            else:
                column += 1
            index += 1

    def highlight_text(self, start, end, node_type):
        if self.query is not None:
            print(f'query[{start}:{end}] = {self.query[start:end]}')
        if node_type in node_types.NODE_TYPES:
            self.text.tag_add(node_type, self.index_map[start], self.index_map[end])
        else:
            self.text.tag_add('OTHER', self.index_map[start], self.index_map[end])

    def clear_highlighting(self):
        for node_type in node_types.NODE_TYPES + ['OTHER']:
            self.text.tag_remove(node_type, '1.0', 'end')

#GUI for displaying the analysis from the tree to the analysis frame
class AnalysisFrame(tk.Frame):
    def __init__(self, root):
        tk.Frame.__init__(self, root)
        self.text_font = font.Font(family='Fira Code Retina', size=12)
        self.text = tk.Text(self, height=10, font=self.text_font)
        
        self.text.grid(row=1, column=0)
        self.scrollbar = tk.Scrollbar(self, orient='vertical', command=self.text.yview)
        self.scrollbar.grid(row=1, column=1, sticky='ns')
        self.text.configure(yscrollcommand=self.scrollbar.set)

        for node_type, color in NODE_COLORS.items():
            self.text.tag_configure(node_type, background=color[0], foreground=color[1])
        self.text.tag_configure('OTHER', background='#ff9800', foreground='black')

        self.index_map = {}
        self.query = None      

    def show_node_info(self, node):
        self.node = node
        raw_json = node.raw_json
        print(raw_json)
        self.text.delete('1.0', 'end')
        idk = ['HASHAGGREGATE',"SORT","NESTED LOOP", "MERGE JOIN", "HASH JOIN", 'SEQ SCAN', 'INDEX SCAN', 'INDEX ONLY SCAN', 'BITMAP INDEX SCAN', 'CTE SCAN']
        if node.id in idk:
            self.text.insert('end', node.aqp_cost)
        else:
            for index, (key, value) in enumerate(raw_json.items()):
                if key == "Node Type":
                    for operations in ATTRIBUTE:
                        if operations == value.upper():
                            operation_type = ATTRIBUTE[operations]
                if key in operation_type:
                    B = str(key) + ": " + str(value) + '\n'
                    self.text.insert('end', B)       

        # for index, (key, value) in enumerate(raw_json.items()):
        #         if key == "Node Type":
        #             for operations in ATTRIBUTE:
        #                 if operations == value.upper():
        #                     operation_type = ATTRIBUTE[operations]
        #         if key in operation_type:
        #             B = str(key) + ": " + str(value) + '\n'
        #             self.text.insert('end', B)
#executing the input query, linking to analysis page
def execute_query(root_widget, query):
    plan = get_json(query)
    plan = plan[2:-2]
    
    plan = json.loads(plan)

    top_level = tk.Toplevel(root_widget)
    
    top_level.title('Visualization')
    top_level.iconphoto(False, tk.PhotoImage(file='tree.png'))
    query = query.replace('\n', ' ')
    query = sqlparse.format(query, reindent=True, keyword_case='upper')
    
    query_frame = QueryFrame(top_level)
    query_frame.set_query(query)

    query_frame.grid(row=0, column=0, sticky='ew')

    analysis_frame = AnalysisFrame(top_level)
    analysis_frame.grid(row=1, column=0, sticky='ew')

    tree_frame =  TreeFrame(top_level)
    tree_frame.grid(row=0, column=1, rowspan=2, sticky = 'w')

    root_node = annotation.build_tree([plan[0]['Plan']])[0]
    match_dict = annotation.build_invert_relation(query, root_node)

    print("jump")
    aggregate = ['HASHAGGREGATE','HASHAGGREGATE']
    sorts = ['SORT', 'SORT']
    loops = ["NESTED LOOP", "MERGE JOIN", "HASH JOIN"]
    scans = ['SEQ SCAN', 'INDEX SCAN', 'INDEX ONLY SCAN', 'BITMAP INDEX SCAN', 'CTE SCAN']
    dict2convert = {"NESTED LOOP":"nestloop", "MERGE JOIN":"mergejoin", "HASH JOIN": "hashjoin", 'SEQ SCAN':'seqscan', 'INDEX SCAN':'indexscan', 'INDEX ONLY SCAN':'indexonlyscan', 'BITMAP INDEX SCAN':'bitmapscan', 'CTE SCAN':'seqscan', 'HASHAGGREGATE':'hashagg', 'CTE SCAN':'tidscan', 'SORT':'sort'}
    cache = {}

    qep_cost = root_node.raw_json['Total Cost']
    for node in PreOrderIter(root_node):
        if node.id in loops:
            permutations = loops
        elif node.id in scans:
            permutations = scans
        elif node.id in aggregate:
            permutations = aggregate
        elif node.id in sorts:
            permutations = sorts
        else:
            continue
        setattr(node, "aqp_cost", "")
        cost = {}
        if node.id in cache:
            cost = cache[node.id]
            keys = list(cost.keys())
            setattr(node, "alternative_costs", cost)
            for key in keys:
                node.aqp_cost += node.id  +" is  "+ str(cost[key]/qep_cost) + " times faster than "+(key if key != "BITMAP INDEX SCAN" else "BITMAP SCAN")+"\n"
        
        else:
            to_exclude = permutations.index(node.id)
            for j in range(len(permutations)):
                if j != to_exclude:
                    disable = ""
                    for k in range(len(permutations)):
                        if k != j:
                            disable += "set enable_" + dict2convert[permutations[k]] + " to off; \n"
                    new_cost = aqp_cost(query, disable)
                    if new_cost not in cost.values() and new_cost != qep_cost:
                        cost[permutations[j]] = new_cost 

            keys = list(cost.keys())
            setattr(node, "alternative_costs", cost)
            cache[node.id] = cost
            for key in keys:
                node.aqp_cost += node.id  +" is  "+ str(cost[key]/qep_cost) + " times faster than "+(key if key != "BITMAP INDEX SCAN" else "BITMAP SCAN")+"\n"
            
        if node.aqp_cost == "":
            node.aqp_cost = "No other alternatives are possible."

    def on_click_listener(node):
        analysis_frame.show_node_info(node)

    def on_hover_listener(node):
        if node in match_dict:
            for start, end in match_dict[node]:
                query_frame.highlight_text(start, end, node.node_type)

    def on_hover_end_listener(node):
        query_frame.clear_highlighting()

    tree_frame.set_on_click_listener(on_click_listener)
    tree_frame.set_on_hover_listener(on_hover_listener)
    tree_frame.set_on_hover_end_listener(on_hover_end_listener)

    tree_frame.draw_tree(root_node)

def aqp_cost(query , permute):
    plan = get_json(query, permute)
    plan = plan[2:-2]
    plan = json.loads(plan)
    root_node = annotation.build_tree([plan[0]['Plan']])[0]
    return root_node.raw_json['Total Cost']

   