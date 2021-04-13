from workflowhub.generator.workflow.abstract_recipe import WorkflowRecipe
import workflowsrasearch 
import workflowsoykb 
import workflowepigenomics 
import workflow1000genome 
import workflowcycles 
import workflowmontage 
import workflowseismology 

import pathlib
import pandas as pd 
import json
import numpy as np

workflows = [
    workflowsrasearch ,
    workflowsoykb ,
    workflowepigenomics ,
    workflow1000genome ,
    workflowcycles ,
    workflowmontage ,
    workflowseismology ,
]

def main():
    for workflow in workflows:
        print(workflow)
        summary = json.loads(pathlib.Path(workflow.__file__).parent.joinpath("microstructures", "summary.json").read_text())
        path = pathlib.Path(workflow.__file__).parent.joinpath("metric", "err.csv")
        if not path.exists():
            continue

        sizes = {base: details["order"] for base, details in summary["base_graphs"].items()}
        df = pd.read_csv(str(path), index_col=0)
        test_cols = [col for col in df.columns[::2]]
        eval_cols = [col for col in df.columns[1::2]]
        assert(len(set(test_cols).intersection(eval_cols)) == 0)

        for col in eval_cols:
            base = min(test_cols, key=lambda b: np.inf if np.isnan(df[col][b]) else abs(sizes[b] - sizes[col]))
            dist = df[col][base] 
            print(col, dist)

        print("-"*20)

if __name__ == "__main__":
    main()