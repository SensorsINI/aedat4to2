# aedat4to2
Convert AEDAT4 files from Inivation's DV https://gitlab.com/inivation/dv/dv-python into AEDAT-2.0 files for jAER https://github.com/SensorsINI/jaer/. 

Based on AEDAT file format specifications in https://inivation.github.io/inivation-docs/Software%20user%20guides/AEDAT_file_formats.html

Python is required (recommend Anaconda).

Started from useful script https://github.com/bald6354/aedat4tomat

# Limitations
aedat4to2 currently only writes DVS brightness change events from aedat4 files. Please request IMU samples and frames by writing
Tobi Delbruck (tobi@ini.uzh.ch).


## Installation
Recommended: Make o use a conda environment.... maybe it is the same one as dv-python uses.
````shell
conda create --name aedat4to2 python=3.8
conda activate aedat4to2
````


Install on system path to run as aedat4to2. Note the -e that allows your edits to aedat4to2.py to instantly have effect.
````shell
pip install -e .
````

## If you just want to develop and not install.

Install the requirements....
````shell
pip install -r requirements.txt
````

## Usage
````console
aedat4to2 -h
usage: aedat4to2 [-h] [-o O] [-i I] [-v]

Convert files from AEDAT-4 to AEDAT-2 format. Either provide a single -i input_file -o output_file, or a list of .aedat4 input files.

optional arguments:
  -h, --help  show this help message and exit
  -o O        output .aedat2 file name
  -i I        input .aedat4 file name
  -v          Turn on verbose output

````

# Example Conversion:
Convert a single file, assuming you run within the module folder aedat4to2
```console
python.exe "aedat4to2/aedat4to2.py" -i sample1.aedat4 -o sample1.aedat2
2021-07-06 09:03:45,939 - __main__ - INFO - sensor size width=346 height=260 (aedat4to2.py:138)
2021-07-06 09:03:46,349 - __main__ - INFO - wrote   1.45e+07 events to sample1.aedat2 (aedat4to2.py:277)
```

Convert a bunch of files from .aedat4 to .aedat2 (assuming you have installed aedat4to2)

````console
aedat4to2 sample1.aedat4 sample2.aedat4
2021-07-06 09:18:06,420 - aedat4to2.aedat4to2 - INFO - sensor size width=346 height=260 (aedat4to2.py:140)
2021-07-06 09:18:06,812 - aedat4to2.aedat4to2 - INFO - wrote   1.45e+07 events to sample1.aedat2 (aedat4to2.py:279)
2021-07-06 09:18:06,819 - aedat4to2.aedat4to2 - INFO - sensor size width=346 height=260 (aedat4to2.py:140)
2021-07-06 09:18:07,210 - aedat4to2.aedat4to2 - INFO - wrote   1.45e+07 events to sample2.aedat2 (aedat4to2.py:279)

````

