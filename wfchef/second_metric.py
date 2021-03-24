import networkx as nx
import argparse
import pathlib 
import json
from typing import Union 
from wfchef.utils import create_graph, annotate
from wfchef.duplicate import duplicate, NoMicrostructuresError
import pickle
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


def compare(synth_graph: nx.DiGraph, real_graph: nx.DiGraph):
    synthetic = {}
    real = {}
    
    for node in synth_graph.nodes:
        type_hash = synth_graph.nodes[node]['type_hash']
        synthetic.setdefault(type_hash, 0)
        synthetic[type_hash] +=1 

    for node in real_graph.nodes:
        type_hash = real_graph.nodes[node]['type_hash']
        real.setdefault(type_hash, 0)
        real[type_hash] +=1 


    type_hashes = ({*synthetic.keys(), *real.keys()})
    mse = sum([
        (real.get(type_hash, 0) / real_graph.order() - synthetic.get(type_hash, 0) / synth_graph.order())**2
        for type_hash in type_hashes
    ]) / len(type_hashes)
    return mse

     
def get_parser()-> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--real", 
        type=pathlib.Path,
        help="Path to real workflows"
    )
    parser.add_argument(
        "--synth", 
        help="Path to synthetic workflows",
        default=None
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="print logs")
    parser.add_argument(
        "-w", "--workflow", 
        choices=[path.stem for path in this_dir.joinpath("microstructures").glob("*") if path.is_dir()],
        help="Workflow to duplicate",
        default=None
    )
    parser.add_argument("--wf-hub", action="store_true", help="if set, the traces are from wfcommons")
    # parser.add_argument("-w", "--wfchef", action="store_true", help="if set, the traces are from wfchef")

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
    verbose = args.verbose


    parser = get_parser()
    args = parser.parse_args()
    verbose = args.verbose
    if (args.synth is None and args.workflow is None) or (args.synth is not None and args.workflow is not None):
        print("You must either provide --synth or --workflow")
        return

    graphs = []
    results = {}

    # Synthetic Workflows to evaluate
    if args.synth is not None:

        workflow: pathlib.Path = pathlib.Path(args.synth)
        if args.wf_hub:
            for wf in workflow.glob("wfcommons*.json"):
                graph = create_graph_wfcommons(wf)
                annotate(graph)
                graph.graph["name"] = wf.stem
                graphs.append(graph)
        else:
            for wf in workflow.glob("old*.json"):
                graph = create_graph(wf)
                annotate(graph)
                graph.graph["name"] = wf.stem
                graphs.append(graph) 

        real_workflows: pathlib.Path = args.real 
        real_graphs = []
        for wf in real_workflows.glob("*.json"):
            graph = create_graph(wf)
            annotate(graph)
            graph.graph["name"] = wf.stem
            real_graphs.append(graph)

        real_sorted_graphs = sorted(real_graphs, key=lambda graph: graph.order())
        synth_sorted_graphs = sorted(graphs, key=lambda graph: graph.order())
        
        labels = [graph.order() for graph in real_sorted_graphs]
        rows = [[None for i in range(len(real_sorted_graphs))]]

        for i, (synth, real) in enumerate(zip(synth_sorted_graphs, real_sorted_graphs)):
            err = compare(real, synth)
            results[real.order()] = err    
            rows[0][i] = err 
            save_results(workflow, results, labels, rows)
    else:      
        workflow: pathlib.Path = this_dir.joinpath("microstructures", args.workflow) 
        summary = json.loads(workflow.joinpath("summary.json").read_text())
        sorted_graphs = sorted([name for name, _ in summary["base_graphs"].items()], key=lambda name: summary["base_graphs"][name]["order"])
        
        
        labels = [summary["base_graphs"][graph]["order"] for graph in sorted_graphs]
        rows = [[None for _ in range(len(sorted_graphs))] for _ in range(len(sorted_graphs))]

        for i, path in enumerate(sorted_graphs[1:], start=1):
            path = workflow.joinpath(path)
            wf_real = pickle.loads(path.joinpath("base_graph.pickle").read_bytes())

            for j, base in enumerate(sorted_graphs[:i+1]):           
                if verbose:
                    print(f"Created real graph ({wf_real.order()} nodes)")
                
                try:
                    wf_synth = duplicate(
                        path=workflow,
                        base=base,
                        num_nodes=wf_real.order(),
                        interpolate_limit=summary["base_graphs"][base]["order"]
                    )
                    dist = compare(wf_synth, wf_real)
                    results.setdefault(wf_real.name, {})
                    results[wf_real.name][wf_synth.name] = {
                            "real": wf_real.order(),
                            "synth": wf_synth.order(),
                            "dist": dist
                        } 
                    rows[j][i] = dist
                except NoMicrostructuresError:
                    print(f"No Microstructures Error")
                    continue   
                
                save_results(workflow, results, labels, rows, square=True)
    



if __name__=="__main__":
    main()

