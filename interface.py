import json
from node_types import ATTRIBUTE
from anytree import PreOrderIter
import sqlparse
import psycopg2
import annotation
import pandas as pd

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
                password="123")
            
            cur = conn.cursor()
            cur.execute(permutations + "EXPLAIN (ANALYZE, VERBOSE, FORMAT JSON)" + inputValue)
            rows = cur.fetchall()
            print(rows)
            x = json.dumps(rows)

            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
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


#GUI for displaying the analysis from the tree to the analysis frame
def show_node_info(node):
    raw_json = node.raw_json
    idk = ['HASHAGGREGATE',"SORT","NESTED LOOP", "MERGE JOIN", "HASH JOIN", 'SEQ SCAN', 'INDEX SCAN', 'INDEX ONLY SCAN', 'BITMAP INDEX SCAN', 'CTE SCAN']
    if node.id in idk:
        return node.aqp_cost
    else:
        for index, (key, value) in enumerate(raw_json.items()):
            if key == "Node Type":
                for operations in ATTRIBUTE:
                    if operations == value.upper():
                        operation_type = ATTRIBUTE[operations]
            if key in operation_type:
                B = str(key) + ": " + str(value) + '\n'
                return B       
  

def execute_query(query):
    plan = get_json(query)
    plan = plan[2:-2]
    
    plan = json.loads(plan)
    query = query.replace('\n', ' ')
    query = sqlparse.format(query, reindent=True, keyword_case='upper')
    root_node = annotation.build_tree([plan[0]['Plan']])[0]
    match_dict = annotation.build_invert_relation(query, root_node)
    print("match_dict",match_dict)
    #aggregate = ['HASHAGGREGATE','HASHAGGREGATE']
    #sorts = ['SORT', 'SORT']
    loops = ["NESTED LOOP", "MERGE JOIN", "HASH JOIN"]
    scans = ['SEQ SCAN', 'INDEX SCAN', 'INDEX ONLY SCAN', 'BITMAP INDEX SCAN', 'CTE SCAN']
    dict2convert = {"NESTED LOOP":"nestloop", "MERGE JOIN":"mergejoin", "HASH JOIN": "hashjoin", 'SEQ SCAN':'seqscan', 'INDEX SCAN':'indexscan', 'INDEX ONLY SCAN':'indexonlyscan', 'BITMAP INDEX SCAN':'bitmapscan', 'CTE SCAN':'seqscan', 'HASHAGGREGATE':'hashagg', 'CTE SCAN':'tidscan', 'SORT':'sort'}
    cache = {}
    node_aqp = []
    qep_cost = root_node.raw_json['Total Cost']
    run_loop = False
    for node in PreOrderIter(root_node):
        if node.id in loops:
            permutations = loops
        elif node.id in scans:
            permutations = scans
        #elif node.id in aggregate:
        #    permutations = aggregate
        #elif node.id in sorts:
        #    permutations = sorts
        else:
            continue
        setattr(node, "aqp_cost", "")
        cost = {node.id: qep_cost}
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
        else:
            if node in match_dict:
                for start, end in match_dict[node]:
                    print(start, end, node.node_type, query[start:end])
                node_aqp += [[node.aqp_cost,start,query[start:end]]]

    keys = list(cache.keys()) #
    scan_df = pd.DataFrame(columns=scans)
    loop_df = pd.DataFrame(columns=loops)


    for key in keys:
        kys = list(cache[key].keys())
        val = list(cache[key].values())
        val = [[v for v in val]]
        

        temp = pd.DataFrame(data=val, columns=kys, index=[key])
        print(temp)
        if key in loops:
            loop_df = pd.concat([loop_df, temp], axis=0)
        else:
            scan_df = pd.concat([scan_df, temp], axis=0) #

    return node_aqp, scan_df, loop_df



def get_all_node_labels(query):
    plan = get_json(query)
    plan = plan[2:-2]
    
    plan = json.loads(plan)
    query = query.replace('\n', ' ')
    query = sqlparse.format(query, reindent=True, keyword_case='upper')
    root_node = annotation.build_tree([plan[0]['Plan']])[0]
    for node in PreOrderIter(root_node):
        try:
            print(show_node_info(node))
        except:
            print(node.id)



def aqp_cost(query , permute):
    plan = get_json(query, permute)
    plan = plan[2:-2]
    plan = json.loads(plan)
    root_node = annotation.build_tree([plan[0]['Plan']])[0]
    return root_node.raw_json['Total Cost']

   