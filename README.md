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

Then to run the metric for the wfchef instances (which duplicates to evaluate) run the command:
```bash
wfchef-metric -v montage 
```
Then to run the metric for the wfhub instances run the command:
```bash
wfhub-metric -v --real path/to/real/montage/jsons --synth path/to/synthetic/montage/jsons 
```
To run for the older generator use the flag "-o" in the previous command:
```bash
wfhub-metric -o -v --real path/to/real/montage/jsons --synth path/to/synthetic/montage/jsons 
```
To run the MSE metric for wfchef instances run the command:
```bash
wfchef-mse -v --real path/to/real/montage/jsons -w montage
```
To run MSE metric for wfhub instances run the command:
```bash
wfchef-mse -v --real path/to/real/montage/jsons --synth path/to/synthetic/montage/jsons --wf-hub
```
To run MSE metric for the old generator instances run the command:
```bash
wfchef-mse -v --real path/to/real/montage/jsons --synth path/to/synthetic/montage/jsons 
```