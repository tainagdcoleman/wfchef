import pathlib
import json
import pickle 
import networkx as nx
from typing import Set, Optional, List
from uuid import uuid4
from wfchef.find_microstructures import draw
import random
import argparse
import pandas as pd 
import math 
from itertools import chain

this_dir = pathlib.Path(__file__).resolve().parent

def duplicate_nodes(graph: nx.DiGraph, nodes: Set[str]):
    new_nodes = {}
    for node in nodes:
        new_node = f"{node}_{uuid4()}"
        graph.add_node(new_node, **graph.nodes[node])
        nx.set_node_attributes(graph, {new_node: node}, "duplicate_of")
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
    
    return new_nodes

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w", "--workflow", 
        choices=[path.stem for path in this_dir.joinpath("microstructures").glob("*") if path.is_dir()],
        required=True,
        help="Workflow to duplicate"
    )
    parser.add_argument(
        "-b", "--base",
        default=None ,
        help="base graph to duplicate off of"
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

def interpolate(xs: List[float], ys: List[float], x: float) -> float:
    if not x in xs:
        xs = [*xs, x]
        ys = [*ys, None]
    ser = pd.Series(ys, index=xs).sort_index()
    ser = ser.interpolate("linear")
    return ser[x]

def main():
    parser = get_parser()
    args = parser.parse_args()

    path = this_dir.joinpath("microstructures", args.workflow)
    summary = json.loads(path.joinpath("summary.json").read_text())

    if args.base:
        base_path = pathlib.Path(args.base)
        if not base_path.is_absolute():
            base_path = path.joinpath(base_path)
    else:
        base_path = path.joinpath(min(summary["base_graphs"].keys(), key=lambda k: summary["base_graphs"][k]["order"]))

    graph = pickle.loads(base_path.joinpath("base_graph.pickle").read_bytes())
    if args.size < graph.order():
        raise ValueError(f"Cannot create synthentic graph with {args.size} nodes from base graph with {graph.order()} nodes")

    microstructures = json.loads(base_path.joinpath("microstructures.json").read_text())

    for ms_hash, ms in microstructures.items():
        idx, values = zip(*summary["frequencies"][ms_hash])
        freq = interpolate(idx, values, args.size)

        for _ in range(int(freq)):
            duplicate_nodes(graph, random.choice(ms["nodes"]))
    
    duplicated = {node for node in graph.nodes if "duplicate_of" in graph.nodes[node]}
    draw(graph, save=args.out, close=True, subgraph=duplicated)

if __name__ == "__main__":
    main()