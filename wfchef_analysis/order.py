from wfchef.utils import create_graph, annotate
import pathlib
import argparse
from typing import List, Union

this_dir = pathlib.Path(__file__).resolve().parent

def order(path: pathlib.Path):
    graphs = []
    for g in path.glob("*.json"):
        graph = create_graph(g)
        annotate(graph)
        graph.graph["name"] = g.stem
        graphs.append(graph)

    sorted_graphs = sorted(graphs, key=lambda graph: graph.order())

    resp = []
    for graph in sorted_graphs:
        # print(f'{graph.name} has order: {graph.order()}')
        resp.append(graph.order())

    return resp 

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "workflow", 
        help="Workflow directory with jsons"
    )
    return parser
        
def main():
    parser = get_parser()
    args = parser.parse_args()
    print(order(pathlib.Path(args.workflow)))

if __name__ == "__main__":
    main()

