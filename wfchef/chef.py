
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
import subprocess

this_dir = pathlib.Path(__file__).resolve().parent

skeleton_path = this_dir.joinpath("skeletons")

def create_recipe(path: Union[str, pathlib.Path], dst: Union[str, pathlib.Path]) -> WorkflowRecipe:
    path = pathlib.Path(path).resolve(strict=True)
    wf_name = f"Workflow{camelcase(path.stem)}"
    dst = pathlib.Path(dst, snakecase(wf_name)).resolve()
    dst.mkdir(exist_ok=True, parents=True)
    
    summary_path = dst.joinpath("microstructures", "summary.json")
    summary_path.parent.mkdir(exist_ok=True, parents=True)
    shutil.copy(path.joinpath("summary.json"), summary_path)
    for filename in ["base_graph.pickle", "microstructures.json"]:
        for p in path.glob(f"*/{filename}"):
            dst_path = dst.joinpath("microstructures", p.parent.stem, filename)
            dst_path.parent.mkdir(exist_ok=True, parents=True)
            shutil.copy(p, dst_path)

    # Recipe 
    with skeleton_path.joinpath("recipe.py").open() as fp:
        skeleton_str = fp.read() 

    skeleton_str = skeleton_str.replace("Skeleton", wf_name)
    skeleton_str = skeleton_str.replace("skeleton", snakecase(wf_name))
    with this_dir.joinpath(dst.joinpath("__init__.py")).open("w+") as fp:
        fp.write(skeleton_str)

    # setup.py 
    with skeleton_path.joinpath("setup.py").open() as fp:
        skeleton_str = fp.read() 
        
    skeleton_str = skeleton_str.replace("Skeleton", wf_name)
    skeleton_str = skeleton_str.replace("skeleton", snakecase(wf_name))
    with this_dir.joinpath(dst.parent.joinpath("setup.py")).open("w+") as fp:
        fp.write(skeleton_str)

    # MANIFEST
    with skeleton_path.joinpath("MANIFEST.in").open() as fp:
        skeleton_str = fp.read() 
        
    skeleton_str = skeleton_str.replace("Skeleton", wf_name)
    skeleton_str = skeleton_str.replace("skeleton", snakecase(wf_name))
    with this_dir.joinpath(dst.parent.joinpath("MANIFEST.in")).open("w+") as fp:
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

    print("Done! To install the package, run: \n")
    print(f"  pip install {dst}")
    print("\nor, in editable mode:\n")
    print(f"  pip install -e {dst}")


if __name__ == "__main__":
    main()

