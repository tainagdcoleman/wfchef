
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

thisdir = pathlib.Path(__file__).resolve().parent

skeleton_path = thisdir.joinpath("recipe_skeleton.py")

def create_recipe(path: Union[str, pathlib.Path], dst: Union[str, pathlib.Path]) -> WorkflowRecipe:
    path = pathlib.Path(path).resolve(strict=True)
    dst = pathlib.Path(dst).resolve()
    dst.mkdir(exist_ok=True, parents=True)

    wf_name = f"Workflow{camelcase(path.stem)}"
    microstructures = json.loads(path.joinpath("microstructures.json").read_text())
    
    shutil.copy(path.joinpath("base_graph.pickle"), dst.joinpath("base_graph.pickle"))
    shutil.copy(path.joinpath("microstructures.json"), dst.joinpath("microstructures.json"))

    with skeleton_path.open() as fp:
        skeleton_str = fp.read() 
    
    args = ["def __init__(self,"]
    init_args = []
    indent_size = 17
    for microstructure in microstructures:
        name = microstructure["name"]
        indent = " "*indent_size
        args.append(f"{indent}{name}: int = 0,")
        init_args.append(f"{name}={name}")

    args_str = "\n".join(args)
    skeleton_str = skeleton_str.replace("Skeleton", wf_name)
    skeleton_str = skeleton_str.replace("SkeletonRecipe", wf_name + "Recipe")
    skeleton_str = skeleton_str.replace("def __init__(self,", args_str)
    skeleton_str = skeleton_str.replace("self._init_()", f"self._init_({','.join(init_args)})")
    
    with thisdir.joinpath(dst.joinpath(snakecase(wf_name)).with_suffix(".py")).open("w+") as fp:
        fp.write(skeleton_str)

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('src')
    parser.add_argument('dst')

    return parser

def main():

    parser = get_parser()
    args = parser.parse_args()
    create_recipe(args.src, args.dst)


if __name__ == "__main__":
    main()

