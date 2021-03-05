# To install dependencies, run:
#   pip install networkx matplotlib
# 
# Then to see all options for the script, run:
#   python wfdraw.py --help
# 
# Examples:
#   python wfdraw.py /path/to/workflow.json -o ./workflow.png
#   python wfdraw.py /path/to/workflow.json --show --labels


import networkx as nx
import pathlib
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.patches as mpatches
from typing import Iterable, Union, Set, Optional, Tuple, Dict, Hashable, List
import argparse
import json
from hashlib import sha256

def string_hash(obj: Hashable) -> str:
    return sha256(str(obj).encode("utf-8")).hexdigest()

def type_hash(_type: str, parent_types: Iterable[str]) -> str:
    return string_hash((_type, sorted(set(parent_types))))

def combine_hashes(*hashes: str) -> str:
    return string_hash(sorted(hashes))

def create_graph(path: pathlib.Path) -> nx.DiGraph:
    with path.open() as fp:
        content = json.load(fp)

        graph = nx.DiGraph()

        # Add src/dst nodes
        graph.add_node("SRC", label="SRC", type="SRC", id="SRC")
        graph.add_node("DST", label="DST", type="DST", id="DST")

        id_count = 0
        for job in content['workflow']['jobs']:
            #specific for epigenomics -- have to think about how to do it in general
            if content['name'] == "genome-dax-0":
                if '_sequence' in job['name']:
                    _type, _id = job['name'].split('_sequence')
                    _id = _id.lstrip('_')
                    if not _id:
                        _id = str(id_count)
                        id_count += 1
                else:
                    _type, _id = job['name'], str(id_count)
                    id_count += 1

                graph.add_node(job['name'], label=_type, type=_type, id=_id)
                    
            else:
                _type, _id = job['name'].split('_ID')
                graph.add_node(job['name'], label=_type, type=_type, id=_id)
     
        # for job in content['workflow']['jobs']:
            for parent in job['parents']:
                graph.add_edge(parent, job['name'])

        for node in graph.nodes:
            
            if node in ["SRC", "DST"]:
                continue
            if graph.in_degree(node) <= 0:
                
                graph.add_edge("SRC", node)
            if graph.out_degree(node) <= 0:
                graph.add_edge(node, "DST")
        
        return graph

def annotate(g: nx.DiGraph) -> None:
    visited = set()
    queue = [(node, 1) for node in g.nodes if g.in_degree(node) <= 0]
    while queue:
        cur, level = queue.pop(0)
        g.nodes[cur]["level"] = level
        g.nodes[cur]["label"] = g.nodes[cur]["id"]
        parent_ths = [
            g.nodes[p]["top_down_type_hash"]
            for p, _ in g.in_edges(cur)
        ]
        g.nodes[cur]["top_down_type_hash"] = type_hash(g.nodes[cur]["type"], parent_ths)

        visited.add(cur)
        queue.extend([
            (child, level + 1) for _, child in g.out_edges(cur)
            if child not in visited and 
            {sib for sib, _ in g.in_edges(child)}.issubset(visited)
        ])

    # REVERSE 
    visited = set()
    queue = [node for node in g.nodes if g.out_degree(node) <= 0]
    while queue:
        cur = queue.pop(0)
        parent_ths = [
            g.nodes[p]["bottom_up_type_hash"]
            for _, p in g.out_edges(cur)
        ]
        g.nodes[cur]["bottom_up_type_hash"] = type_hash(g.nodes[cur]["type"], parent_ths)
        g.nodes[cur]["type_hash"] = combine_hashes(g.nodes[cur]["top_down_type_hash"], g.nodes[cur]["bottom_up_type_hash"])

        visited.add(cur)
        queue.extend([
            child for child, _ in g.in_edges(cur)
            if child not in visited and 
            {sib for _, sib in g.out_edges(child)}.issubset(visited)
        ])

def draw(g: nx.DiGraph, 
         with_labels: bool = False, 
         ax: Optional[plt.Axes] = None,
         show: bool = False,
         save: Optional[Union[pathlib.Path, str]] = None,
         close: bool = False,
         subgraph: Set[str] = set()) -> Tuple[plt.Figure, plt.Axes]:
    fig: plt.Figure
    ax: plt.Axes
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 10))
    else:
        fig = ax.get_figure()

    pos = nx.nx_agraph.pygraphviz_layout(g, prog='dot')
    type_set = sorted({g.nodes[node]["type"] for node in g.nodes})
    types = {
        t: i for i, t in enumerate(type_set)
    }
    node_color = [types[g.nodes[node]["type"]] for node in g.nodes]
    for node in g.nodes:
        if node in subgraph:
            g.nodes[node]["node_shape"] = "s"
        else:
            g.nodes[node]["node_shape"] = "c"
    edgecolors = [("green" if node in subgraph else "white") for node in g.nodes]
    edge_color = [
        "green" if src in subgraph and dst in subgraph else "black"
        for src, dst in g.edges
    ]
    cmap = cm.get_cmap('rainbow', len(type_set))
    nx.draw(g, pos, node_color=node_color, edgecolors=edgecolors, edge_color=edge_color, linewidths=3, cmap=cmap, ax=ax, with_labels=with_labels)
    color_lines = [mpatches.Patch(color=cmap(types[t]), label= t) for t in type_set]
    legend = ax.legend(handles = color_lines , loc='lower right')

    # for handle in legend.legendHandles:
    #     handle.set_color(cmap(types[t]))

    if show:
        plt.show()

    if save is not None:
        fig.savefig(str(save))

    if close:
        plt.close(fig)

    return fig, ax