import networkx as nx
from typing import Tuple, Optional, List
from wfchef.utils import create_graph, annotate, draw
from wfchef.duplicate import duplicate
import argparse
import pathlib 
import numpy as np

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
        'path', 
        help="Path to the real Workflow (json) to compare against", 
        type=pathlib.Path
    )
    parser.add_argument(
        "-w", "--workflow", 
        choices=[path.stem for path in this_dir.joinpath("microstructures").glob("*") if path.is_dir()],
        required=True,
        help="Workflow to duplicate"
    )
    
    
    return parser



def main():
    parser = get_parser()
    args = parser.parse_args()


    workflow = this_dir.joinpath("microstructures", args.workflow)
    
    
    wf_real = create_graph(args.path)
    annotate(wf_real)
    print(f"Created real graph ({wf_real.order()} nodes)")

    wf_synth = duplicate(
        microstructure=workflow.joinpath("microstructures.json"),
        base_graph=workflow.joinpath("base_graph.pickle"),
        nodes=wf_real.order(),
        complex=False
    )

    nx.write_gml(wf_real,  workflow.joinpath(f'real.gml'), stringizer=str)
    nx.write_gml(wf_synth, workflow.joinpath(f'synth.gml'), stringizer=str)

    draw(wf_synth, extension='png', save=this_dir.joinpath("synth.png"), close=True)

    print(f"Created synthetic graph with {wf_synth.order()} nodes")


    print(compare(wf_real, wf_synth))
    print(compare(wf_real, wf_real))


    
if __name__ == "__main__":
    main()