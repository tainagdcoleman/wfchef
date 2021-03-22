# Pipeline 

## Installation
To clone and install wfchef:
```bash
https://github.com/tainagdcoleman/wfchef.git
pip install -e ./wfchef  # -e optional (for editable mode)
``` 

## Running 

First to find the microstructures and save them as jsons run this command:
```bash
wfchef-find-microstructures path/to/montage/jsons -n montage -v
```

Then to run the metric (which duplicates to evaluate) run the command:
```bash
wfchef-metric montage -v
```
