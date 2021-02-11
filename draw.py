import networkx as nx
import pathlib
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.patches as mpatches
from typing import Iterable, Union, Set, Optional, Tuple, Dict, Hashable, List
import argparse
import json


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



def draw(g: nx.DiGraph, 
        with_labels: bool = False, 
        ax: Optional[plt.Axes] = None,
        show: bool = False,
        save: Optional[Union[pathlib.Path, str]] = None,
        close: bool = False) -> Tuple[plt.Figure, plt.Axes]: 
    
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
    cmap = cm.get_cmap('rainbow', len(type_set))
    nx.draw(g, pos, node_color=node_color, linewidths=3, cmap=cmap, ax=ax, with_labels=with_labels)
    color_lines = [mpatches.Patch(color=cmap(types[t]), label= t) for t in type_set]
    legend = ax.legend(handles = color_lines , loc='lower right')

  
    if show:
        plt.show()

    if save is not None:
        fig.savefig(str(save))

    if close:
        plt.close(fig)

    return fig, ax

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('src')
    parser.add_argument('dst')

    return parser

def main():

    parser = get_parser()
    args = parser.parse_args()
    args.src = pathlib.Path(args.src)
    args.dst = pathlib.Path(args.dst)
    graph = create_graph(args.src)

    draw(graph, show=True, save=args.dst)

if __name__ == "__main__":
    main()