import pathlib
import json
import pickle 
import networkx as nx
from typing import Set
from uuid import uuid4
from find_microstructures import draw
import random

this_dir = pathlib.Path(__file__).resolve().parent

def duplicate_nodes(graph: nx.DiGraph, nodes: Set[str]):
    new_nodes = {}
    for node in nodes:
        new_node = f"{node}_{uuid4()}"
        graph.add_node(new_node, duplicate_of=node, **graph.nodes[node])
        new_nodes[node] = new_node
    
    for node, new_node in new_nodes.items():
        for parent, _ in graph.in_edges(node):
            if parent in new_nodes:
                graph.add_edge(new_nodes[parent], new_node)
            else:
                graph.add_edge(parent, new_node)

        for _, child in graph.out_edges(node):
            if child in new_nodes:
                graph.add_edge(new_node, new_nodes[child])
            else:
                graph.add_edge(new_node, child)


def duplicate(microstructure: pathlib.Path, base_graph: pathlib.Path, nodes: int) -> nx.DiGraph:
    microstructure = pathlib.Path(microstructure).resolve()
    base_graph = pathlib.Path(base_graph).resolve()

    mdata = json.loads(microstructure.read_text())
    graph: nx.DiGraph = pickle.loads(base_graph.read_bytes())

    while len(graph.nodes) < nodes:
        duplicate_nodes(graph, random.choice(mdata[0]["nodes"]))

    return graph


def main():

    path = this_dir.joinpath("microstructures", "cycles")
    graph = duplicate(path.joinpath("microstructures.json"), path.joinpath("base_graph.pickle"), 100)
    
    duplicated = {node for node in graph.nodes if "duplicate_of" in graph.nodes[node]}
    draw(graph, save=this_dir.joinpath("duplicated.png"), close=True, subgraph=duplicated)



    
if __name__ == "__main__":
    main()