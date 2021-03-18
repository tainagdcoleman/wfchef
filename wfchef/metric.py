import networkx as nx
from typing import Tuple, Optional, List
from wfchef.utils import create_graph, annotate, draw
from wfchef.duplicate import duplicate
import argparse
import pathlib 
import numpy as np
import json
import pickle 

this_dir = pathlib.Path(__file__).resolve().parent

def compare_on(graph1: nx.DiGraph, graph2: nx.DiGraph, attr: str) -> float:
    return next(nx.optimize_graph_edit_distance(
            graph1, graph2, 
            node_match=lambda x, y: x[attr] == y[attr], 
            node_del_cost=lambda *x: 1.0, node_ins_cost=lambda *x: 1.0, 
            edge_del_cost=lambda *x: 1.0, edge_ins_cost=lambda *x: 1.0
        )
    )


def compare(graph1: nx.DiGraph, graph2: nx.DiGraph):
    v = compare_on(graph1, graph2, "type_hash")
    i = compare_on(graph1, graph2, "id")
    print(f"{v}/{i}")
    return np.inf if i == 0 else v / i


def get_parser()-> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "workflow", 
        choices=[path.stem for path in this_dir.joinpath("microstructures").glob("*") if path.is_dir()],
        help="Workflow to duplicate"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="print logs")
    return parser

def plot_metric(graph1: str, graph2: str, dist: float):
    pass


def main():
    parser = get_parser()
    args = parser.parse_args()
    verbose = args.verbose

    workflow = this_dir.joinpath("microstructures", args.workflow)
    summary = json.loads(workflow.joinpath("summary.json").read_text())
    sorted_graphs = sorted([name for name, _ in summary["base_graphs"].items()], key=lambda name: summary["base_graphs"][name]["order"])

    results = {}
    for i, path in enumerate(sorted_graphs[1:], start=1):
        if verbose:
            print(f"TEST {i} ({path})")
        path = workflow.joinpath(path)
        wf_real = pickle.loads(path.joinpath("base_graph.pickle").read_bytes())
        results.setdefault(wf_real.name, {})

        for base in sorted_graphs[:i+1]:           
            if verbose:
                print(f"Created real graph ({wf_real.order()} nodes)")
            
            wf_synth = duplicate(
                path=workflow,
                base=base,
                num_nodes=wf_real.order()
            )
            dist = compare(wf_real, wf_synth)
            results[wf_real.name][wf_synth.name] = {
                "real": wf_real.order(),
                "synth": wf_synth.order(),
                "base": summary['base_graphs'][base]['order'],
                "dist": dist
            }
 
            if verbose:
                print(f"Created synthetic graph with {wf_synth.order()} nodes from {summary['base_graphs'][base]['order']}-node graph ({base})")
                print(dist)
                print()

        workflow.joinpath("results").with_suffix(".json").write_text(json.dumps(results, indent=2)) 


    
if __name__ == "__main__":
    main()