import networkx as nx
from hashlib import sha256
from typing import Iterable, Union, Set, Optional, Tuple, Dict, Hashable, List
from uuid import uuid4
import pathlib
import os
import json
import traceback
from itertools import product
from networkx.readwrite import read_gpickle, write_gpickle
import numpy as np 
from itertools import chain, combinations
import argparse
from .utils import create_graph, string_hash, type_hash, combine_hashes, annotate, draw


this_dir = pathlib.Path(__file__).resolve().parent

def find_microstructure(graph: nx.DiGraph, node: str, sibling: str, ms = None, ms_sibling = None):
    if ms is None:
        ms, ms_sibling = set(), set()
    if node == sibling: 
        return ms, ms_sibling
    ms.add(node)
    ms_sibling.add(sibling)
    key = lambda node: graph.nodes[node]["type_hash"]
    childs1 = sorted([child for _, child in graph.out_edges(node)], key=key)
    childs2 = sorted([child for _, child in graph.out_edges(sibling)], key=key)
    for child1, child2 in zip(childs1, childs2):
        _ms, _ms_sibling = find_microstructure(graph, child1, child2, ms, ms_sibling)
        ms.update(_ms)
        ms_sibling.update(_ms_sibling)
    return ms, ms_sibling

def get_frequencies(graphs: List[nx.DiGraph]) -> Tuple[Dict[str, List[int]], Dict[int, int]]:
    types = {}
    size = {}
    for i, graph in enumerate(graphs):
        size[i] = graph.order()
        for node in graph.nodes:
            types.setdefault(graph.nodes[node]["type"], [0]*len(graphs))
            types[graph.nodes[node]["type"]][i] += 1
    return types, size

def find_microstructures(workflow_path: Union[pathlib.Path], 
                         savedir: pathlib.Path, 
                         verbose: bool = False, 
                         do_combine: bool = False,
                         img_type: str = "png",
                         highlight_all_instances: bool = False,
                         include_trivial: bool = False):
    if verbose:
        print(f"Working on {workflow_path}")
    graphs = []
    for path in workflow_path.glob("*.json"):
        graph = create_graph(path)
        annotate(graph)
        graph.graph["name"] = path.stem
        graphs.append(graph)
    
    if not graphs:
        raise ValueError(f"No graphs found in {workflow_path}")

    if verbose:
        print("Constructed graphs")
    
    sorted_graphs = sorted(graphs, key=lambda graph: len(graph.nodes))
    g = sorted_graphs[0]  # smallest graph
    freqs, sizes = get_frequencies(sorted_graphs)
    get_freqs = lambda root_types: np.min([freqs[root_type] for root_type in root_types], axis=0).tolist()
    nx.set_node_attributes(g, {node: set() for node in g.nodes}, name="microstructures")

    savedir = pathlib.Path(savedir)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
    savedir.mkdir(exist_ok=True, parents=True)

    # Save smallest graph to disk for loading later
    base_graph_path = savedir.joinpath("base_graph.pickle")
    write_gpickle(g, str(base_graph_path))

    if verbose:
        print("Drawing base graph")
    draw(g, with_labels=False, save=str(savedir.joinpath(f"base_graph.{img_type}")))

    if verbose:
        print("Finding microstructures")
    visited = set()
    queue = ["SRC"]
    microstructures = {}
    while queue:
        node = queue.pop()
        visited.add(node)
        children = [child for _, child in g.out_edges(node)]
        for s1, s2 in combinations(children, r=2):
            if s1 == s2 or g.nodes[s1]["type_hash"] != g.nodes[s2]["type_hash"]: 
                continue 

            if verbose:
                print(f"RUNNING {s1}/{s2}")
            _g = g.copy()
            duplicated, s2_duplicated = find_microstructure(_g, s1, s2)
            ms_hash = combine_hashes(*[_g.nodes[n]["type_hash"] for n in duplicated])
            for node in duplicated:
                g.nodes[node]["microstructures"].add(ms_hash)
            ms_size = len(duplicated)
            microstructures.setdefault(ms_hash, (ms_size, _g.nodes[s1]["type"], []))
            microstructures[ms_hash][2].append(set(duplicated)) 
            microstructures[ms_hash][2].append(set(s2_duplicated)) 
    
        queue.extend(children) 

    if do_combine:
        merged = {}
        for ms_hash, (ms_size, root_type, node_sets) in microstructures.items():
            idxs = []
            for merged_hash, (_, _, _node_sets) in merged.items():
                ms_nodes = frozenset(chain(*node_sets))
                _ms_nodes = frozenset(chain(*_node_sets))

                if ms_nodes.intersection(_ms_nodes) not in [set(), ms_nodes, _ms_nodes]:
                    idxs.append(merged_hash) # at least one node in common
            
            if not idxs:
                merged[ms_hash] = (ms_size, {root_type}, node_sets)
            else:
                new_nodes = []
                for all_nodes in product(node_sets, *[merged[merged_hash][2] for merged_hash in idxs]): # product between all 
                    if all([len(n1.intersection(n2)) > 0 for n1, n2 in combinations(all_nodes, r=2)]):
                        new_nodes.append(set.union(*all_nodes))

                root_types = {root_type, *chain(*[merged[merged_hash][1] for merged_hash in idxs])}
                merged[combine_hashes(ms_hash, merged_hash)] = (len(new_nodes[0]), root_types, new_nodes)
                for merged_hash in idxs:
                    del merged[merged_hash]
    else:
        merged = {ms_hash: (ms_size, {root_type}, node_sets) for ms_hash, (ms_size, root_type, node_sets) in microstructures.items()}
    
    sorted_microstructures = sorted(
        [
            (ms_size, ms_root_types, ms) for _, (ms_size, ms_root_types, ms) 
            in merged.items() 
            if include_trivial or np.unique(get_freqs(ms_root_types)).size > 1 or len(get_freqs(ms_root_types)) == 1 # remove microstructures with no duplication
        ], 
        key=lambda x: x[0]
    )

    mdatas = []
    for i, (ms_size, ms_root_types, duplicated) in enumerate(sorted_microstructures):
        correlations = {}
        
        for j, (_, key, _) in enumerate(sorted_microstructures):
            if i == j:
                continue
            correlations[f"microstructure_{j}"] = np.corrcoef(get_freqs(ms_root_types), get_freqs(key))[0,1]
        
        mdata = {
            "name": f"microstructure_{i}",
            "nodes": list(map(list, duplicated)),
            "size": ms_size,
            "frequencies": dict(zip(sizes.values(), get_freqs(ms_root_types))),
            "base_graph_path": str(base_graph_path.relative_to(savedir)),
            "correlations": correlations
        }

        mdatas.append(mdata)   
        draw(
            g, 
            subgraph=duplicated[0] if not highlight_all_instances else set.union(*duplicated),
            with_labels=False, 
            save=str(savedir.joinpath(f"microstructure_{i}.{img_type}")), 
            close=True
        )

    type_hashes = {
        ms["name"]: {g.nodes[node]["type_hash"] for node in ms["nodes"][0]}
        for ms in mdatas
    }
    for ms in mdatas:
        ms["simple"] = True
        for _ms in mdatas:

            inter = type_hashes[ms["name"]].intersection(type_hashes[_ms["name"]])
            if inter not in (set(), type_hashes[ms["name"]], type_hashes[_ms["name"]]):
                ms["simple"] = False
        
    with savedir.joinpath(f"microstructures.json").open("w+") as fp:
        json.dump(mdatas, fp, indent=2)
            

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help="Directory of workflow JSONs", type=pathlib.Path)
    parser.add_argument("-v", "--verbose", action="store_true", help="print logs")
    parser.add_argument("-n", "--name", help="name for workflow")
    parser.add_argument("-c", "--combine", action="store_true", help="if true, run microstructure combining algorithm")
    parser.add_argument("-t", "--image-type", default="png", help="output types for images. anything that matplotlib supports (png, jpg, pdf, etc.)")
    parser.add_argument("-l", "--highlight-all-instances", action="store_true", help="if set, highlights all instances of the microstructure")
    parser.add_argument("-i", "--include-trivial", action="store_true", help="if set, trivial microstructures are not filtered out")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    outpath = this_dir.joinpath("microstructures", args.name)
    find_microstructures(
        args.path, outpath, args.verbose, args.combine, args.image_type.lower(),
        highlight_all_instances=args.highlight_all_instances,
        include_trivial=args.include_trivial
    )

if __name__ == "__main__":
    main()
    