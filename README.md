# Pipeline 

## Installation
To clone and install wfchef:
```bash
https://github.com/tainagdcoleman/wfchef.git
pip install -e ./wfchef  # -e optional (for editable mode)
``` 

## Running 
If running wfchef for the first time, or if instances were added, to find the microstructures and save them as jsons run this command:
```bash
wfchef-find-microstructures -v path/to/montage/jsons -n montage 
```

To run the metric for the wfchef if you do not have the traces yet (this will call duplicate to evaluate) run the command:
```bash
wfchef-dist -v montage 
```
To run the metric for wfhub, generator and wfchef when the traces are already available run the command:
```bash
wfchef-metric -v --real path/to/real/montage/jsons --synth path/to/synthetic/montage/jsons 
```
To run the RMSE metric for wfchef, wfhub and generator traces:
```bash
wfchef-rmse -v --real path/to/real/montage/jsons --synth path/to/synthetic/montage/jsons
```
