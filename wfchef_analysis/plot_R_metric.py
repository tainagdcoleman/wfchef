import plotly.express as px
import plotly.graph_objects  as go
import pandas as pd
import pathlib
from pathlib import Path
from plotly.subplots import make_subplots
import numpy as np
from plotly import tools


this_dir = pathlib.Path(__file__).resolve().parent
data = this_dir.joinpath('experiments_other.csv')

savedir = this_dir.joinpath("plots")
savedir.mkdir(exist_ok=True, parents=True)

def plot_energy_makespan(df: pd.DataFrame, model: str):


    algs = ["EnReal", "SPSS-EB", "IOBalance"] if model == "realistic" else ["EnReal", "SPSS-EB"]
    df = df[df["algorithm"].isin(algs)] 

    _model = ["realistic"] if model == "realistic" else ["realistic", "traditional"]
    df = df[df["model"].isin(_model)]

    df["algorithm/model"] = df["algorithm"] + "/" + df["model"]

    df = pd.melt(
        df, 
        id_vars=[c for c in df.columns if c not in ["energy", "makespan"]],
        var_name="metric", value_name="value"
    )

    fig = px.bar(
        df,
        x="tasks",
        y="value",
        facet_col="workflow",
        facet_row="metric",
        color="algorithm/model",
        facet_col_spacing=0.05,
        facet_row_spacing=0.1,
        barmode="group",
        color_discrete_sequence=["#ffbc42","#d81159","#8f2d56","#218380","#73d2de"],
        labels={
            "value": "",
            "tasks": "# tasks"
        }
    )

    labels = {"energy": "energy (kWh)", "makespan": "makespan (s)"}
    fig.for_each_annotation(lambda a: None if not a.text.startswith("metric=") else a.update(xanchor="left", x=-0.05, textangle=270))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.for_each_annotation(lambda a: a.update(text=labels.get(a.text, a.text)))

    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.05,
        xanchor="right",
        x=0.8
    ))

    fig.update_yaxes(matches=None)
    fig.update_xaxes(matches=None)
    fig.update_yaxes(showticklabels=True)
    fig.update_xaxes(showticklabels=True)
    fig.update_layout(yaxis = dict(tickfont = dict(size=18)))
    fig.update_xaxes(
        tickangle = 45,
        title_font = {"size": 18})
    
    fig.update_layout(
        font_family="Courier",
        font_size=18,
        showlegend=True
    )

    fig.write_html(str(this_dir.joinpath(f"energy_{model}.html")))

def main():
    df = pd.read_csv(data) 

    df["energy"] /= 1000 #KWh
    df["energy"] = np.sqrt(df["energy"]) 
    df = df.sort_values(["tasks"])

    df = df[(df["workflow"] != "1000Genome") | (df["tasks"] > 250)]    
    df["tasks"] = df["tasks"].astype(str)
    df["model"].replace({"unpaired": "realistic"}, inplace=True)
    df["algorithm"].replace({"IOAware-Balance": "IOBalance"}, inplace=True)
    df.drop_duplicates(subset=['workflow', 'algorithm', 'model', 'tasks'], keep='first', inplace=True)

    for model in ["traditional", "realistic"]:
        plot_energy_makespan(df.copy(), model)
    
    
if __name__ == "__main__":
    main()
