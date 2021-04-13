import pathlib
import pandas as pd
import numpy as np 
import os
import plotly.express as px
import argparse
import plotly.graph_objects as go
import plotly


thisdir = pathlib.Path(__file__).resolve().parent
plotly.io.orca.config.executable = "/home/tainagdcoleman/anaconda3/envs/wfhub/bin/orca" # '/usr/bin/orca'

def nan_diagonal(df):
    for col in df.columns:
        n = int(str(col).split(".")[0])
        df.loc[n, col] = np.nan 
    return df
        
def to_int(names):
    return [int(str(col).split(".")[0]) for col in names]

def merge_series(sers):
    idx_counts = {}
    for ser in sers:
        ser.index = to_int(ser.index)
        _idx_counts = {}
        for v in ser.index:
            _idx_counts.setdefault(v, 0)
            _idx_counts[v] += 1
        for v, c in _idx_counts.items():
            idx_counts.setdefault(v, 0)
            idx_counts[v] = max(_idx_counts[v], idx_counts[v])
                
    idx = sorted([v for v, c in idx_counts.items() for i in range(c)])
    vs = {}
    for ser in sers:
        vs[ser.name] = []
        for i, count in idx_counts.items():
            try:
                vals = ser.loc[i]
                vals = [vals] if not isinstance(vals, pd.Series) else vals.values.tolist()
            except KeyError:
                vals = []
                
            vs[ser.name].extend(vals + [None]*(count - len(vals))) 
            
    df = pd.DataFrame(vs, index=idx)
    return df

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('-w','--workflow', help="Path to workflow metric directory to plot")
    parser.add_argument('-m','--metric', help="Which metric are you ploting: mse or edit_dist")
    parser.add_argument('-e','--extension', help="extension of the metric file: err or dist")
    parser.add_argument('-c','--csv', help="path to the csv file")

    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    
    if args.csv:
        path_csv = pathlib.Path(args.csv)

        df = pd.read_csv(path_csv)
        df["tool"].replace({"generator": "Gen2014"}, inplace=True)
        df["tool"].replace({"workflowhub": "WorkflowHub"}, inplace=True)
        df["tool"].replace({"wfchef": "WfChef"}, inplace=True)
        


        df["num_tasks"] = df["num_tasks"].astype(int)
        df = df.sort_values(["num_tasks"])
        df = df[df["num_tasks"] != df["num_tasks"].min()]
        
        if "makespan" in path_csv.stem:
            df["tool"].replace({"real": "Real"}, inplace=True)
            df["makespan"] += df["makespan"].max() * 0.01
            fig = px.bar(
                df,
                x="num_tasks",
                y="makespan",
                color="tool",
                barmode="group",
                color_discrete_sequence=["#41817f","#F5BF5A","#843555","#C62E5A"],
                labels={
                    "makespan": "makespan(s)",
                    "num_tasks": "#tasks"
                }
            )
            fig.update_layout(title = path_csv.stem.split("-")[0])
            
        else:
            fig = px.bar(
                df,
                x="num_tasks",
                y="rmspe_start",
                color="tool",
                barmode="group",
                color_discrete_sequence=["#F5BF5A","#843555","#C62E5A"],
                labels={
                    "rmspe_start": "RMSPE",
                    "num_tasks": "#tasks"
                }
            )
            fig.update_layout(title = path_csv.stem)

        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=0.8,
            font_size=28,
        ))
        fig.update_layout({'legend_title_text': ''})
        fig.update_layout(
            font_size=28,
            showlegend=True,
            plot_bgcolor="#ebebeb",
        )
        fig.update_xaxes(
            tickangle = -45,
            title_font = {"size": 28},
            showgrid=True,
            type = "category")
        
        fig.update_yaxes(
            title_font = {"size": 28},
            showgrid=True)

        fig.write_html(str(thisdir.joinpath(f"scripts_Rafael/{path_csv.stem}.html")))  
        fig.write_image(str(thisdir.joinpath(f"scripts_Rafael/{path_csv.stem}.pdf")),width=1650, height=700)      

    if args.workflow:
        path = pathlib.Path(args.workflow)

        workflow = path.stem  
        metric = args.metric
        ext = args.extension
        
        csv_path = path.joinpath(metric, f"wfchef_base_samples_{ext}.csv")
        if ext == "err":
            mc_path = path.joinpath(metric, f"mc.csv")
            csv_path = mc_path
            mc_df = pd.read_csv(csv_path, index_col=0).drop(["run", "name"], axis=1)
            if workflow == "montage":
                mc_df = mc_df[mc_df["num_tasks"] != mc_df["num_tasks"].min()]
            mc_df["num_tasks"] = mc_df["num_tasks"].astype(str)
            wfchef = mc_df.groupby(["num_tasks"]).median().squeeze()
            wfchef = wfchef[~wfchef.index.duplicated(keep="first")].sort_index()
            wfchef_q1 = mc_df.groupby(["num_tasks"]).quantile(0.25).squeeze()
            wfchef_q1 = wfchef_q1[~wfchef_q1.index.duplicated(keep="first")].sort_index()
            wfchef_q3 = mc_df.groupby(["num_tasks"]).quantile(0.75).squeeze()
            wfchef_q3 = wfchef_q3[~wfchef_q3.index.duplicated(keep="first")].sort_index()
            wfchef_min = mc_df.groupby(["num_tasks"]).min().squeeze()
            wfchef_min = wfchef_min[~wfchef_min.index.duplicated(keep="first")].sort_index()
            wfchef_max = mc_df.groupby(["num_tasks"]).max().squeeze()
            wfchef_max = wfchef_max[~wfchef_max.index.duplicated(keep="first")].sort_index()
        else:
            wfchef: pd.Series = pd.read_csv(csv_path, index_col=0).round(6).iloc[0] 
            wfchef = wfchef[~wfchef.index.str.contains("\.")]

        wfchef.name = "WfChef"

        wfcommons = pd.read_csv(path.joinpath(metric, f"wfhub_{ext}.csv"), index_col=0).round(6).iloc[0]
        wfcommons.name = "WorkflowHub"
        wfcommons = wfcommons[~wfcommons.index.str.contains("\.")]

        all_index = set(wfchef.index.values).intersection(wfcommons.index.values)
        offset = max(wfchef.max()*0.01, wfcommons.max()*0.01)
        
        generator_path = path.joinpath(metric, f"generator_{ext}.csv")
        if generator_path.exists():
            generator = pd.read_csv(generator_path, index_col=0).round(6).iloc[0]
            generator.name = "Gen2014"
            generator = generator[~generator.index.str.contains("\.")]
            
            all_index = all_index.intersection(generator.index.values)
            generator = generator[generator.index.isin(all_index)]

            offset = max(offset, generator.max()*0.01)
            generator += offset

        wfchef = wfchef[wfchef.index.isin(all_index)]
        wfcommons = wfcommons[wfcommons.index.isin(all_index)]
        wfchef += offset
        wfcommons += offset
        
        
        fig = go.Figure()
        if generator_path.exists():
            fig.add_trace(go.Bar(
                x=generator.index.values, y=generator.values, 
                name=generator.name, marker={'color':"#F5BF5A"}
            ))
        
        if csv_path.stem == "mc":
            fig.add_trace(go.Bar(
                x=wfchef.index.values, y=wfchef.values, 
                name=wfchef.name, marker={'color': "#843555"},
                error_y=dict(
                    type='data', 
                    array=(wfchef_q3 - wfchef).values.tolist(),
                    arrayminus=(wfchef - wfchef_q1).values.tolist()
                )
                
            ))
            fig.add_trace(go.Scatter(
                x=wfchef_min.index.values, y=wfchef_min.values, 
                name=wfchef.name, marker={'color': "black"},
                mode='markers',
                showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=wfchef_max.index.values, y=wfchef_max.values, 
                name=wfchef.name, marker={'color': "black"},
                mode='markers',
                showlegend=False
            ))
        else:
            fig.add_trace(go.Bar(
                x=wfchef.index.values, y=wfchef.values, 
                name=wfchef.name, marker={'color': "#843555"}
            ))

        fig.add_trace(go.Bar(
            x=wfcommons.index.values, y=wfcommons.values, 
            name=wfcommons.name, marker={'color': "#C62E5A"}
        ))

        if metric == 'mse':
            fig.update_layout(title=workflow,
                        xaxis_title='#tasks',   
                        yaxis_title='Type Hash Frequency (THF)',
                        
            )
        else:
            fig.update_layout(title=workflow,
                        xaxis_title='#tasks',   
                        yaxis_title='Approximate Edit Distance (AED)',
                        
            )

        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=0.8,
            font_size=28,
        ))
        fig.update_layout(
            font_size=28,
            showlegend=True,
            plot_bgcolor="#ebebeb",
        )
        fig.update_xaxes(
            tickangle = -45,
            title_font = {"size": 28},
            showgrid=True)

        fig.write_image(str(path.joinpath(str(f"{path.stem}.pdf"))), width=1650, height=700)



if __name__ == '__main__':
    main()
