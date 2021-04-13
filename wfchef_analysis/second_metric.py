import networkx as nx
import argparse
import pathlib 
import json
from typing import Union 
from wfchef.utils import create_graph, annotate
import pandas as pd 
import numpy as np
from wfchef.chef import compare_rmse

this_dir = pathlib.Path(__file__).resolve().parent
     
def get_parser()-> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--real", 
        type=pathlib.Path,
        required=True,
        help="Path to real workflows"
    )
    parser.add_argument(
        "--synth", 
        type=pathlib.Path,
        required=True,
        help="Path to synthetic workflows"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="print logs")
    # parser.add_argument("--gen", action="store_true", help="if set, the traces are from generator")
    # parser.add_argument("--wfhub", action="store_true", help="if set, the traces are from wfhub")

    return parser

def save_results(path: Union[str, pathlib.Path], results, labels, rows, square: bool = False):     
    savedir = path.joinpath('metric')
    savedir.mkdir(exist_ok=True, parents=True)

    savedir.joinpath("err.json").write_text(json.dumps(results, indent=2)) 
    if square:
        df = pd.DataFrame(rows, columns=labels, index=labels)
    else:
        df = pd.DataFrame(rows, columns=labels)
    df = df.dropna(axis=1, how='all')
    df = df.dropna(axis=0, how='all')
    savedir.joinpath("err.csv").write_text(df.to_csv())

def main():
    parser = get_parser()
    args = parser.parse_args()

    graphs = []
    results = {}

    # Synthetic Workflows to evaluate
    workflow: pathlib.Path = pathlib.Path(args.synth)
    wfs = [*workflow.glob("old*.json"), *workflow.glob("wfcommons*.json"), *workflow.glob("wfchef*.json")]
    for wf in wfs:
        graph = create_graph(wf)
        annotate(graph)
        graph.graph["name"] = wf.stem
        graphs.append(graph) 

    # pprint.pprint({graph.nodes[node]["type"] for graph in graphs for node in graph.nodes})

    real_workflows: pathlib.Path = args.real 
    real_graphs = []
    for wf in real_workflows.glob("*.json"):
        graph = create_graph(wf)
        annotate(graph)
        graph.graph["name"] = wf.stem
        real_graphs.append(graph)

    # return
    real_sorted_graphs = sorted(real_graphs, key=lambda graph: graph.order())
    synth_sorted_graphs = sorted(graphs, key=lambda graph: graph.order())

    pairs = [
        (
            real_graph, 
            synth_sorted_graphs[np.argmin([abs(synth_graph.order() - real_graph.order()) for synth_graph in synth_sorted_graphs])]
        )
        for real_graph in real_sorted_graphs
    ]

    labels = [graph.order() for graph in real_sorted_graphs]
    rows = [[None for i in range(len(real_sorted_graphs))]]
    for i, (synth, real) in enumerate(pairs):
        err = compare_rmse(real, synth)
        results[real.order()] = err    
        rows[0][i] = err 
        save_results(workflow, results, labels, rows)
    



if __name__=="__main__":
    main()



#colors: "#F5BF5A", "#C62E5A", "#843555", #ebebeb