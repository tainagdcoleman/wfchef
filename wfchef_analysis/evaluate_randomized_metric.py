from numpy.lib.npyio import save
import pandas as pd 
from wfchef.chef import compare_rmse, find_err
from typing import Dict
import argparse

from wfchef.utils import annotate
from recipe_to_json import workflows, create_graph, get_parser
import pathlib

import time 

thisdir = pathlib.Path(__file__).resolve().parent

# def get_parser() -> argparse.ArgumentParser:
#     parser = argparse.ArgumentParser()
#     parser.add_argument("-w", "--workflow", choices=workflows.keys(), required=True)
#     parser.add_argument("--runs", type=int, default=1, help="number of runs to generate. Default is one.")
#     return parser

def get_graphs(path: pathlib.Path):
    return sorted([(g.stem, create_graph(g)) for g in path.glob("*.json")], key=lambda e: e[1].order())

def main():
    parser = get_parser()
    args = parser.parse_args()

    if args.save is None:
        savedir = pathlib.Path("wfchef_metric_results", time.strftime("%m.%d.%Y"), args.workflow, "mse")
    else:
        savedir = pathlib.Path(args.save)

    savedir.mkdir(exist_ok=True, parents=True)
    Recipe = workflows[args.workflow]
    columns = ["run", "num_tasks", "name", "rmse"]
    rows = []
    for run in range(args.runs):
        Recipe = workflows[args.workflow]
        for i, (name, graph) in enumerate(get_graphs(args.base_on)):
            annotate(graph)
            try:
                synth_graph = Recipe.generate_nx_graph(graph.order(), exclude_graphs=[name])
            except ValueError:
                print(f"Skipping {name}")
                continue
            rmse = compare_rmse(synth_graph, graph)
            rows.append([run, graph.order(), name, rmse])

            df = pd.DataFrame(rows, columns=columns)
            df.to_csv(str(savedir.joinpath("mc.csv")))
            print(name, rmse)
            

if __name__ == "__main__":
    main()