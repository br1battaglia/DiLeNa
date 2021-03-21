import networkx
from networkx.algorithms.components.connected import connected_components
import requests
import multiprocessing as mp
import datetime
import sys
import time
import json
from collections import defaultdict

transList = []
nodeSet = set()

def to_edges(node):
    it = iter(node)
    last = next(it)
    for current in it:
        yield last, current
        last = current

def multiInputHeuristic(node):
    G = networkx.Graph()
    for part in node:
        # each sublist is a bunch of nodes
        G.add_nodes_from(part)
        # it also imlies a number of edges:
        prova = to_edges(part)
        if len(list(prova)) > 0:
            G.add_edges_from(to_edges(part))
    return G

test = [[1,2], [2,3,4], [6,3], [9,10,23], [38], [4,38]]
G = multiInputHeuristic(test)
print(list(connected_components(G))) 



""" tx = requests.get('https://sochain.com/api/v2/address/BTC/36FaKKQiU8MaLcz3eDBbJsQSx5ify4hqDY')
tx = tx.json()
for i in tx['data']['inputs']:
    nodeSet.add(i['address'])
    for o in tx['data']['outputs']:
        nodeSet.add(o['address'])
        transList.append (Transaction(i['address'], o['address'], 0))  """

""" tx = requests.get('https://sochain.com/api/v2/address/BTC/36FaKKQiU8MaLcz3eDBbJsQSx5ify4hqDY')
tx = tx.json()
if 'outgoing' in tx['data']['txs'][0]:
    print("OK")


with open('res/test.net', 'w', encoding='utf-8') as f:
    json.dump(tx, f, ensure_ascii=False, indent=4) 
    for t in tx:
        print(t, file = f)
 """


######################## Other way to compute multi input heuristic

"""
G = multiInputHeuristic(test)
print(list(connected_components(G))) """ 
""" def multiInputHeuristic(lists):
    neighbors = defaultdict(set)
    seen = set()
    for each in lists:
        for item in each:
            neighbors[item].update(each)
    def component(node, neighbors=neighbors, seen=seen, see=seen.add):
        nodes = set([node])
        next_node = nodes.pop
        while nodes:
            node = next_node()
            see(node)
            nodes |= neighbors[node] - seen
            yield node
    for node in neighbors:
        if node not in seen:
            yield sorted(component(node))

test = [[1,2], [2], [6], [9], [38], [4]]
print(list(connected_components(test))) """