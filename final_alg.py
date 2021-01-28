import networkx as nx
from hashlib import sha256
from typing import Iterable, Union, Set, Optional, Tuple, Dict, Hashable, List
from uuid import uuid4
import pathlib
import os
import json
import traceback
from itertools import product
import shutil
from networkx.readwrite import read_gpickle, write_gpickle


this_dir = pathlib.Path(__file__).resolve().parent

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

def string_hash(obj: Hashable) -> str:
    return sha256(str(obj).encode("utf-8")).hexdigest()

def type_hash(_type: str, parent_types: Iterable[str]) -> str:
    return string_hash((_type, sorted(set(parent_types))))

def combine_hashes(*hashes: str) -> str:
    return string_hash(sorted(hashes))


def annotate(g: nx.DiGraph) -> None:
    visited = set()
    queue = [(node, 1) for node in g.nodes if g.in_degree(node) <= 0]
    while queue:
        cur, level = queue.pop(0)
        g.nodes[cur]["level"] = level
        g.nodes[cur]["label"] = g.nodes[cur]["id"]
        parent_ths = [
            g.nodes[p]["type_hash"]
            for p, _ in g.in_edges(cur)
        ]
        g.nodes[cur]["type_hash"] = type_hash(g.nodes[cur]["type"], parent_ths)

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
            g.nodes[p]["r_type_hash"]
            for _, p in g.out_edges(cur)
        ]
        g.nodes[cur]["r_type_hash"] = type_hash(g.nodes[cur]["type"], parent_ths)
        g.nodes[cur]["combined_type_hash"] = combine_hashes(g.nodes[cur]["type_hash"], g.nodes[cur]["r_type_hash"])

        visited.add(cur)
        queue.extend([
            child for child, _ in g.in_edges(cur)
            if child not in visited and 
            {sib for _, sib in g.out_edges(child)}.issubset(visited)
        ])
    

def find_microstructure(graph: nx.DiGraph, node: str, sibling: str):
    new_nodes = {}
    dup_root, added = _find_microstructure(graph, node, sibling, new_nodes)
    added.update({par for par, _ in graph.in_edges(node)})
    for parent, _ in graph.in_edges(node):
        graph.add_edge(parent, dup_root)
    return dup_root, added, new_nodes

def _find_microstructure(graph: nx.DiGraph, cur1: str, cur2: str, new_nodes: Dict[str, str]) -> Tuple[str, Set[str]]:
    if cur1 == cur2:
        return cur1, {cur1}
    elif cur1 in new_nodes:
        return new_nodes[cur1], {new_nodes[cur1]}

    new_id = uuid4()
    new_node = f"{cur1}_{uuid4()}"
    graph.add_node(
        new_node,
        id=new_id, 
        type=graph.nodes[cur1]["type"],
        type_hash=graph.nodes[cur1]["type_hash"], 
        r_type_hash=graph.nodes[cur1]["r_type_hash"],
        combined_type_hash=graph.nodes[cur1]["combined_type_hash"],
        level=graph.nodes[cur1]["level"],
        duplicate_of=cur1
    )
    new_nodes[cur1] = new_node

    childs1 = sorted(
        [child for _, child in graph.out_edges(cur1)], 
        key=lambda node: graph.nodes[node]["combined_type_hash"]
    )
    childs2 = sorted(
        [child for _, child in graph.out_edges(cur2)], 
        key=lambda node: graph.nodes[node]["combined_type_hash"]
    )

    added = {new_node}
    for child1, child2 in zip(childs1, childs2):
        _new_child, _new_added = _find_microstructure(graph, child1, child2, new_nodes)
        graph.add_edge(new_node, _new_child)
        added.update(_new_added)

    return new_node, added


import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.patches as mpatches

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
    type_set = {g.nodes[node]["type"] for node in g.nodes}
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

def get_frequencies(graphs: List[nx.DiGraph]) -> Dict[str, List[int]]:
    types = {}
    for i, graph in enumerate(graphs):
        for node in graph.nodes:
            types.setdefault(graph.nodes[node]["type"], [0]*len(graphs))
            types[graph.nodes[node]["type"]][i] += 1
    return types

def main(verbose: bool = False):
    paths = [
        pathlib.Path('/home/tainagdcoleman/pegasus-traces/cycles'),
        pathlib.Path('/home/tainagdcoleman/pegasus-traces/1000genome'),
        pathlib.Path('/home/tainagdcoleman/pegasus-traces/montage'),
        pathlib.Path('/home/tainagdcoleman/pegasus-traces/soykb')
    ]
    for workflow_path in paths:
        if verbose:
            print(f"Working on {workflow_path}")
        graphs = []
        for path in workflow_path.glob("*/*.json"):
            graph = create_graph(path)
            annotate(graph)
            graph.graph["name"] = path.stem
            graphs.append(graph)
        
        sorted_graphs = sorted(graphs, key=lambda graph: len(graph.nodes))
        g = sorted_graphs[0]  # smallest graph
        freqs = get_frequencies(sorted_graphs)
    
        savedir = this_dir.joinpath("microstructures", workflow_path.stem)  
        if savedir.exists():
            shutil.rmtree(savedir)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
        savedir.mkdir(exist_ok=True, parents=True)

        # Save smallest graph to disk for loading later
        base_graph_path = savedir.joinpath("base_graph.pickle")
        write_gpickle(g, str(base_graph_path))

        draw(g, with_labels=False, save=str(savedir.joinpath("base_graph.png")))

        visited = set()
        queue = ["SRC"]
        microstructures = {}
        while queue:
            node = queue.pop()
            visited.add(node)
            children = [child for _, child in g.out_edges(node)]
            for s1, s2 in product(children, children):
                if s1 == s2 or g.nodes[s1]["type_hash"] != g.nodes[s2]["type_hash"]: 
                    continue 

                if verbose:
                    print(f"RUNNING {s1}/{s2}")
                _g = g.copy()
                dup_root, _, new_nodes = find_microstructure(_g, s1, s2)
                duplicated = {old_node for old_node, new_node in new_nodes.items()}
                microstructures[_g.nodes[dup_root]["type_hash"]] = (_g.nodes[dup_root]["type"], duplicated) 
        
            queue.extend([child for child in children if child not in visited])
        
        sorted_microstructures = sorted(
            [v for _, v in microstructures.items()], 
            key=lambda x: len(x[1])
        )
        for i, (dup_root_type, duplicated) in enumerate(sorted_microstructures):
            mdata = {
                "nodes": list(duplicated),
                "size": len(duplicated),
                "frequencies": freqs[dup_root_type],
                "base_graph_path": str(base_graph_path.relative_to(savedir)) 
            }
            with savedir.joinpath(f"microstructure_{i}.json").open("w+") as fp:
                json.dump(mdata, fp, indent=2)

            draw(
                g, 
                subgraph=duplicated,
                with_labels=False, 
                save=str(savedir.joinpath(f"microstructure_{i}.png")), 
                close=True
            )

if __name__ == "__main__":
    main()