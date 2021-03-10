import networkx as nx
from typing import Tuple, Optional, List
from wfchef.utils import create_graph, annotate
from wfchef.duplicate import duplicate
import argparse
import pathlib 
import gmatch4py as gm



this_dir = pathlib.Path(__file__).resolve().parent


def compare_distance(wf1: nx.DiGraph, wf2: nx.DiGraph) -> int:
    return nx.graph_edit_distance(wf1, wf2)

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
    print(f"Created real graph ({wf_real.order()} nodes)")
    wf_synth = duplicate(
        microstructure=workflow.joinpath("microstructures.json"),
        base_graph=workflow.joinpath("base_graph.pickle"),
        nodes=wf_real.order(),
        save_dir=None,
        complex=False
    )
    print(f"Created synthetic graph with {wf_synth.order()} nodes")
    annotate(wf_real)
    print(f"Annotated real graph ")
    annotate(wf_synth)
    print(f"Annotated synthetic graph ")

    # print("Comparison: ", compare_paths(wf_real, wf_synth))
    # nodes_wf1 = wf1.nodes()
    # nodes_wf2 = wf2.nodes()


    dist = nx.graph_edit_distance(
        wf_real, wf_synth, 
        roots=("SRC", "SRC"),
        node_match=lambda n1, n2: n1["type_hash"] == n2["type_hash"]
    )
    print(dist)

    # ged=gm.GraphEditDistance(1,1,1,1) # all edit costs are equal to 1
    # result=ged.compare([wf_real,wf_synth],None) 

    # print(result)


    
if __name__ == "__main__":
    main()