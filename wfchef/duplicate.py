import pathlib
import json
import pickle 
import networkx as nx
from typing import Set
from uuid import uuid4
from .find_microstructures import draw
import random
import argparse

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


def duplicate(microstructure: pathlib.Path, base_graph: pathlib.Path, nodes: int, complex: bool = False) -> nx.DiGraph:
    microstructure = pathlib.Path(microstructure).resolve()
    base_graph = pathlib.Path(base_graph).resolve()

    mdata = json.loads(microstructure.read_text())
    graph: nx.DiGraph = pickle.loads(base_graph.read_bytes())

    if not complex:
        mdata = [ms for ms in mdata if ms["simple"]]
    
    if not mdata:
        if not complex:
            raise ValueError("Worflow has no simple microstructures")
        else:
            raise ValueError("Worflow has no microstructures")

    i = 0
    while len(graph.nodes) < nodes:
        duplicate_nodes(graph, random.choice(mdata[i % len(mdata)]["nodes"]))
        i += 1

    return graph

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w", "--workflow", 
        choices=[path.stem for path in this_dir.joinpath("microstructures").glob("*") if path.is_dir()],
        required=True,
        help="Workflow to duplicate"
    )
    parser.add_argument(
        "-s", "--size", type=int,
        help="Approximate size of graph to generate"
    )
    parser.add_argument(
        "-o", "--out", type=pathlib.Path,
        help="path to save graph image to"
    )
    parser.add_argument(
        "-c", "--complex", action="store_true",
        help="Duplicate complex microstructures - this may not result in accurate looking graphs."
    )

    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()

    path = this_dir.joinpath("microstructures", args.workflow)
    graph = duplicate(path.joinpath("microstructures.json"), path.joinpath("base_graph.pickle"), args.size, args.complex)
    
    duplicated = {node for node in graph.nodes if "duplicate_of" in graph.nodes[node]}
    draw(graph, save=args.out, close=True, subgraph=duplicated)



    
if __name__ == "__main__":
    main()