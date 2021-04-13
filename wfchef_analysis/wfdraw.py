import networkx as nx
import pathlib
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.patches as mpatches
from typing import Iterable, Union, Set, Optional, Tuple, Dict, Hashable, List
import argparse
import json
from networkx.generators.atlas import THIS_DIR
from wfchef.utils import create_graph, draw

this_dir = pathlib.Path(__file__).resolve().parent



def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('src', help="Path to workflow json to plot")
    parser.add_argument("-s", "--show", action="store_true", help="If set, shows the plot")
    parser.add_argument("-o", "--out", help="file to save plot")
    parser.add_argument("-e", "--extension", default="png", help="extension of the image, default is PNG")
    parser.add_argument("-l", "--labels", action="store_true", help="If set, write labels for nodes on plot")

    return parser

def main():

    parser = get_parser()
    args = parser.parse_args()
    args.src = pathlib.Path(args.src)
    graph = create_graph(args.src)

    draw(graph, save=args.out, extension=args.extension, show=args.show, with_labels=args.labels, close=True)

if __name__ == "__main__":
    main()