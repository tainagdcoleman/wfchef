import networkx as nx
from typing import Union
import argparse
import pathlib 
import json
from wfchef.utils import annotate, create_graph
import pandas as pd

this_dir = pathlib.Path(__file__).resolve().parent

def create_graph_wfcommons(path: Union[str, pathlib.Path]) -> nx.DiGraph:
    path = pathlib.Path(path)
    with path.open() as fp: 
        content = json.load(fp)
        graph = nx.DiGraph()
        # Add src/dst nodes
        graph.add_node("SRC", label="SRC", type="SRC", id="SRC")
        graph.add_node("DST", label="DST", type="DST", id="DST")
        id_count = 0
        
        for job in content['workflow']['jobs']:         
            _type, _id = job['name'].split('_0')
            graph.add_node(job['name'], label=_type, type=_type, id=_id)
            
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

def compare_on(synth: nx.DiGraph, real: nx.DiGraph, attr: str) -> float:
    return next(nx.optimize_graph_edit_distance(
            real, synth, 
            node_match=lambda x, y: x[attr] == y[attr], 
            node_del_cost=lambda *x: 1.0, node_ins_cost=lambda *x: 1.0, 
            edge_del_cost=lambda *x: 1.0, edge_ins_cost=lambda *x: 1.0
        )
    )

def compare(synth: nx.DiGraph, real: nx.DiGraph):
    approx_num_edits = compare_on(synth, real, "type")
    return approx_num_edits / real.size()

def get_parser()-> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--real", 
        type=pathlib.Path,
        help="Path to real workflows"
    )
    parser.add_argument(
        "--synth", 
        type=pathlib.Path,
        help="Path to synthetic workflows"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="print logs")
    parser.add_argument("-o", "--old", action="store_true", help="if set, the traces are from the old generator")
    parser.add_argument("--no-cache", action="store_true", help="if set, everything is recomputed from scratch")

    return parser
   
def main():
    parser = get_parser()
    args = parser.parse_args()
    verbose = args.verbose
    
    #Workflows to evaluate
    if args.old:
        workflow: pathlib.Path = args.synth 
        graphs = []
        for wf in workflow.glob("old*.json"):
            graph = create_graph(wf)
            annotate(graph)
            graph.graph["name"] = wf.stem
            graphs.append(graph) 
    else:
        workflow: pathlib.Path = args.synth 
        graphs = []
        for wf in workflow.glob("wfcommons*.json"):
            graph = create_graph_wfcommons(wf)
            annotate(graph)
            graph.graph["name"] = wf.stem
            graphs.append(graph)
    
        
    synth_sorted_graphs = sorted(graphs, key=lambda graph: graph.order())

    #Real workflows
    real_workflows: pathlib.Path = args.real 
    real_graphs = []
    for wf in real_workflows.glob("*.json"):
        graph = create_graph(wf)
        annotate(graph)
        graph.graph["name"] = wf.stem
        real_graphs.append(graph)

    real_sorted_graphs = sorted(real_graphs, key=lambda graph: graph.order())
    metric_dir = workflow.joinpath('metric')
    metric_dir.mkdir(parents=True, exist_ok=True)
    results_path = metric_dir.joinpath("results.json")
    labels = [f"{graph} ({graph.order()})" for graph in real_sorted_graphs]
    labels = [graph.order()for graph in real_sorted_graphs]
    rows = [[None for _ in range(len(real_sorted_graphs))]] # for _ in range(len(real_sorted_graphs))]

    results = {}
    if not args.no_cache and results_path.is_file():
        results = json.loads(results_path.read_text())

    for i, (wf_synth, wf_real) in enumerate(zip(synth_sorted_graphs, real_sorted_graphs)):
        dist = results.get(wf_real.name, {}).get(wf_synth.name, {}).get("dist")
        not_in_cache = dist is None
        if not_in_cache:
            dist = compare(wf_synth, wf_real)
            
        results.setdefault(wf_real.name, {})
        results[wf_real.name][wf_synth.name] = {
                "real": wf_real.order(),
                "synth": wf_synth.order(),
                "dist": dist
            } 
        rows[0][i] = dist
        
        if not_in_cache: # if it's cached, no need to write
            results_path.write_text(json.dumps(results, indent=2)) 
            df = pd.DataFrame(rows, columns=labels)
            df = df.dropna(axis=1, how='all')
            df = df.dropna(axis=0, how='all')
            workflow.joinpath("results.csv").write_text(df.to_csv())
    

   

if __name__ == "__main__":
    main()