from anytree import AnyNode, PreOrderIter
import node_types
import copy 
import re 

# recursive function to build tree based on extracted json file 
def build_tree(plan_list, parent=None):
    result_list = []
    for plan in plan_list: 
        node_type = plan['Node Type'].upper() 

        # set node 
        if parent is None: 
            node = AnyNode(id = node_type, node_type=node_type) 
        else: 
            node = AnyNode(id = node_type, node_type=node_type, parent=parent)

        # Setting the key attributes that are going to be used for searching later
        if node_type in node_types.KEY_PROPERTY:
            key_properties = node_types.KEY_PROPERTY[node_type]
            for key_property in key_properties:
                if key_property in plan:
                    setattr(node, key_property, plan[key_property])

        # if "Output" in plan:
        #     setattr(node, "Output", plan["Output"])
        raw_json = copy.deepcopy(plan)
        if "Plans" in plan:
            build_tree(plan["Plans"], node)  # Build sub tree recursive call 
            raw_json.pop("Plans")  # Don't put the entire subtree in the raw json
        if "Partial Mode" in plan:
            setattr(node, "Partial Mode", plan["Partial Mode"])
        if "Index Name" in plan:
            setattr(node, "Index Name", plan["Index Name"])
        setattr(node, "raw_json", raw_json)
        result_list.append(node)
        
    return result_list

def build_relation(query_formatted, tree):
    """
    Build relation between plan and query by iterating the tree
    Match a given token to all nodes that contain this token
    """
    match_dict = {}  # {(start index of token, end): [list of matched nodes]}
    tokens = tokenize_query(query_formatted)
    for token, position in tokens.items():
        match_dict[(position[0], position[1])] = search_tree(token, tree)

    return match_dict


def build_invert_relation(query_formatted, tree):
    """
    Build relation between plan and query by iterating the tree
    Match a given node to all tokens that correlate
    """
    match_dict = {}  # Has structure {node object : [list of tuples of index]}
    tokens = tokenize_query(query_formatted)
    for node in PreOrderIter(tree):
        if getattr(node, 'id') not in node_types.KEY_PROPERTY:
            continue
        else:
            for field in node_types.KEY_PROPERTY[getattr(node, 'id')]:
                if not hasattr(node, field):
                    continue
                value = getattr(node, field)
                matched_pos = search_query(value, tokens, query_formatted)
                if matched_pos is not None:
                    if node in match_dict:
                        match_dict[node] = match_dict[node] + matched_pos
                    else:
                        match_dict[node] = matched_pos
    return match_dict


def search_tree(token, root):
    """
    Do the search by using built-in pre-order iteration
    Return a list of matched nodes or None if no node matched
    """
    matched_pos = []
    for node in PreOrderIter(root):
        # If a node is not defined in our searchable list, skip it
        if getattr(node, 'id') not in node_types.KEY_PROPERTY:
            continue
        else:
            for field in node_types.KEY_PROPERTY[getattr(node, 'id')]:
                if not hasattr(node, field):
                    continue
                value = getattr(node, field)
                if token in str(value):
                    matched_pos.append(node)

    if len(matched_pos) == 0:
        return None
    else:
        return matched_pos


def search_query(value, tokens, query_formatted):
    """
    Do full text search on query
    Return a list of index tuple of matched query tokens or None if no token matched
    """
    matched_pos = []
    if isinstance(value, list):
        for v in value:
            regex_matches = re.finditer(v, query_formatted)
            for match in regex_matches:
                matched_pos.append((match.start(), match.end()))
    else:
        regex_matches = re.finditer(str(value).strip('()'), query_formatted)
        for match in regex_matches:
            matched_pos.append((match.start(), match.end()))

    for token, position in tokens.items():  # position is a tuple of (start idx, end idx)
    
        # Assume value can be either a list of string or a string. Could it also be dict?
        if isinstance(value, list):  # value is a list of string
            for v in value:
                if token in v:
                    matched_pos.append(position)
                    break
        else:  # value is string
            if token in str(value):
                matched_pos.append(position)

    if len(matched_pos) == 0:
        return None
    else:
        return matched_pos


def tokenize_query(query_formatted):
    """
    Tokenize query, return a dictionary with structure {token: (start index in query, end index..)}
    No keyword included in the result
    """
    tokens = {}
    lines = query_formatted.splitlines()  # Process query line by line
    processed_lines_len = 0
    for i in range(len(lines)):
        if i > 0:
            # +1 because of newline character has length 1
            processed_lines_len += len(lines[i - 1]) + 1

        tokenized_line = re.split('[ (),]', lines[i])
        print('tokenized line: ' + str(tokenized_line))
        for token in tokenized_line:
            token = token.strip(';')
            if token.upper() != '' and token.upper() not in node_types.KEYWORDS:
                regex_matches = re.finditer(r'([ (,])' + token + '($| |\)|,)', lines[i])
                for matched in regex_matches:
                    tokens[token] = (matched.start() + processed_lines_len, matched.end() + processed_lines_len)
                    print('appending token: ' + token + ', pos: ' + str(tokens[token]))
                # index_in_query = lines[i].index(token) + processed_lines_len
                # tokens[token] = (index_in_query, index_in_query + len(token))

    print('Tokens:' + str(tokens))
    return tokens