
import pathlib
import json
from workflowhub.generator.workflow.abstract_recipe import WorkflowRecipe, Workflow
from typing import Optional, Union, Dict, Any
import types
from pprint import pprint
import argparse
import shutil
from stringcase import camelcase, snakecase
from logging import Logger

this_dir = pathlib.Path(__file__).resolve().parent

skeleton_path = this_dir.joinpath("recipe_skeleton.py")

def create_recipe(path: Union[str, pathlib.Path], dst: Union[str, pathlib.Path]) -> WorkflowRecipe:
    path = pathlib.Path(path).resolve(strict=True)
    dst = pathlib.Path(dst).resolve()
    dst.mkdir(exist_ok=True, parents=True)

    wf_name = f"Workflow{camelcase(path.stem)}"
    # microstructures = json.loads(path.joinpath("microstructures.json").read_text())
    
    summary_path = dst.joinpath("microstructures", "summary.json")
    summary_path.parent.mkdir(exist_ok=True, parents=True)
    shutil.copy(path.joinpath("summary.json"), summary_path)
    for filename in ["base_graph.pickle", "microstructures.json"]:
        for p in path.glob(f"*/{filename}"):
            dst_path = dst.joinpath("microstructures", p.parent.stem, filename)
            dst_path.parent.mkdir(exist_ok=True, parents=True)
            shutil.copy(p, dst_path)

    with skeleton_path.open() as fp:
        skeleton_str = fp.read() 
    
    # args = ["def __init__(self,"]
    # init_args = []
    # indent_size = 17
    # for microstructure in microstructures:
    #     name = microstructure["name"]
    #     indent = " "*indent_size
    #     args.append(f"{indent}{name}: int = 0,")
    #     init_args.append(f"{name}={name}")

    # args_str = "\n".join(args)
    skeleton_str = skeleton_str.replace("Skeleton", wf_name)
    # skeleton_str = skeleton_str.replace("def __init__(self,", args_str)
    # skeleton_str = skeleton_str.replace("self._init_()", f"self._init_({','.join(init_args)})")
    
    with this_dir.joinpath(dst.joinpath(snakecase(wf_name)).with_suffix(".py")).open("w+") as fp:
        fp.write(skeleton_str)

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
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
    src = this_dir.joinpath("microstructures", args.workflow)
    dst = src.joinpath("recipe")
    create_recipe(src, dst)


if __name__ == "__main__":
    main()

