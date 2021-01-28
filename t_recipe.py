
import pathlib
import yaml
from workflowhub.generator.workflow.abstract_recipe import WorkflowRecipe, Workflow
from typing import Optional, Union, Dict, Any
import types
from pprint import pprint
import argparse

from logging import Logger

thisdir = pathlib.Path(__file__).resolve().parent

skeleton_path = pathlib.Path("/home/tainagdcoleman/tests/recipe_skeleton.py")

def create_recipe(path: Union[str, pathlib.Path], dst: Union[str, pathlib.Path]) -> WorkflowRecipe:
    path = pathlib.Path(path).resolve(strict=True)
    dst = pathlib.Path(dst).resolve()
   
    with path.open() as fp:
        structure = yaml.load(fp, Loader=yaml.SafeLoader)
    

    with skeleton_path.open() as fp:
        skeleton_str = fp.read() 
    
    args = ["def __init__(self,"]
    init_args = []
    indent_size = 17
    for name, (low, high) in structure["variables"].items():
        indent = " "*indent_size
        args.append(f"{indent}{name}: int = {low},")
        init_args.append(f"{name}={name}")
w
    args_str = "\n".join(args)
    skeleton_str = skeleton_str.replace("Skeleton", structure["name"])
    skeleton_str = skeleton_str.replace("SkeletonRecipe", structure["name"] + "Recipe")
    skeleton_str = skeleton_str.replace("def __init__(self,", args_str)
    skeleton_str = skeleton_str.replace("self._init_()", f"self._init_({','.join(init_args)})")
    
    skeleton_str = skeleton_str.replace("structure = {}", "structure = " + str(structure))

    with thisdir.joinpath(dst.with_suffix(".py")).open("w+") as fp:
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

