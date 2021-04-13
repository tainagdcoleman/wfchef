from typing import Dict
from workflowhub.generator.workflow.abstract_recipe import WorkflowRecipe
from workflowsrasearch import WorkflowsrasearchRecipe
from workflowsoykb import WorkflowsoykbRecipe
from workflowepigenomics import WorkflowepigenomicsRecipe
from workflow1000genome import Workflow1000genomeRecipe
from workflowcycles import WorkflowcyclesRecipe
from workflowmontage import WorkflowmontageRecipe
from workflowseismology import WorkflowseismologyRecipe
import pathlib
from argparse import ArgumentParser
from wfchef.utils import create_graph, annotate
import math 

this_dir = pathlib.Path(__file__).resolve().parent

def graph_orders(path: pathlib.Path):
    return sorted([(g.stem, create_graph(g).order()) for g in path.glob("*.json")], key=lambda e: e[1])

workflows: Dict[str, WorkflowRecipe] = {
    "srasearch": WorkflowsrasearchRecipe,
    "soykb": WorkflowsoykbRecipe,
    "epigenomics": WorkflowepigenomicsRecipe,
    "1000genome": Workflow1000genomeRecipe,
    "cycles":  WorkflowcyclesRecipe,
    "montage": WorkflowmontageRecipe,
    "seismology": WorkflowseismologyRecipe,
}

def get_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("-w", "--workflow", choices=workflows.keys(), required=True)
    parser.add_argument("--base-on", required=True, type=pathlib.Path, help="directory with traces to duplicate same size graphs for.")
    parser.add_argument("--save", default=None, help="path to save jsons to. Default is ./<workflow>-savedir")
    parser.add_argument("--runs", type=int, default=1, help="number of runs to generate. Default is one.")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()

    _savedir = this_dir.joinpath(f"{args.workflow}-recipes") if args.save is None else pathlib.Path(args.save)

    zpad = math.ceil(math.log(args.runs, 10))
    for run in range(args.runs):
        savedir = _savedir if args.runs <= 1 else _savedir.joinpath(f"wfchef_run_{str(run).zfill(zpad)}")
        savedir.mkdir(parents=True, exist_ok=True)

        Recipe = workflows[args.workflow]
        for i, (name, order) in enumerate(graph_orders(args.base_on)):
            try:
                recipe = Recipe.from_num_tasks(order, exclude_graphs=[name])
            except ValueError:
                print(f"Skipping: {name}")
                continue
            wf = recipe.build_workflow()
            file = savedir.joinpath(f'wfchef_{args.workflow}_{order}_{i}.json')
            wf.write_json(str(file)) 


if __name__ == "__main__":
    main()