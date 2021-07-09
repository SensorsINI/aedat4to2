# aedat4to2
Convert AEDAT4 files from Inivation's DV https://gitlab.com/inivation/dv/dv-python into AEDAT-2.0 files for jAER https://github.com/SensorsINI/jaer/. 

Based on AEDAT file format specifications in https://inivation.github.io/inivation-docs/Software%20user%20guides/AEDAT_file_formats.html

Python is required (recommend Anaconda).

Started from useful script https://github.com/bald6354/aedat4tomat

### Sample of jAER output from converted file from Baldwin dataset
![bike_sample](https://github.com/SensorsINI/aedat4to2/blob/master/sample-jaer-output.png "Sample AEDAT-2.0 output")

# Limitations
aedat4to2 now supports DVS events, IMU samples, and APS frames. Please report bugs using issue tracker.


## Installation
Recommended: Make o use a conda environment.... maybe it is the same one as dv-python uses.
````shell
conda create --name aedat4to2 python=3.8
conda activate aedat4to2
````

To install directly from git into your activated conda environment
````console
pip install git+https://github.com/SensorsINI/aedat4to2.git
````

From clone, install on system path to run as aedat4to2. Note the -e that allows your edits to aedata4to2/aedat4to2.py to instantly have effect.
````shell
pip install -e .
````

## If you just want to develop and not install.

Install the requirements....
````shell
pip install -r requirements.txt
````

### Windows DV users
If you have not installed DV, you might need to go through one-time installation of
MS visual studio build tools to install DV which depends on a package that does not supply pre-built binaries.

## Usage
````console
aedat4to2 -h
usage: aedat4to2 [-h] [-o O] [-i I] [-q] [-v] [--overwrite] [--no_imu] [--no_frame]

Convert files from AEDAT-4 to AEDAT-2 format. Either provide a single -i input_file -o output_file, or a list of .aedat4 input files.

optional arguments:
  -h, --help   show this help message and exit
  -o O         output .aedat2 file name
  -i I         input .aedat4 file name
  -q           Turn off all output other than warnings and errors
  -v           Turn on verbose output
  --overwrite  Overwrite existing output files
  --no_imu     Do not process IMU samples (which are very slow to extract)
  --no_frame   Do not process APS sample frames (which are very slow to extract)
````

# Example Conversion:
Convert a single file, assuming you run within the module folder aedat4to2
```console
aedat4to2 --overwrite aedat4to2\sample1.aedat4
2021-07-08 16:09:30,273 - aedat4to2.aedat4to2 - INFO - overwriting F:\tobi\Dropbox (Personal)\GitHub\SensorsINI\aedat4to2\sample1.aedat2 (aedat4to2.py:163)
2021-07-08 16:09:30,274 - aedat4to2.aedat4to2 - INFO - sensor size width=346 height=260 (aedat4to2.py:173)
2021-07-08 16:09:30,564 - aedat4to2.aedat4to2 - INFO - 3635159 DVS events (aedat4to2.py:220)
frames: 992 fr [00:00, 4488.69 fr/s]
2021-07-08 16:09:30,814 - aedat4to2.aedat4to2 - INFO - 992 frames with size (346, 260) (aedat4to2.py:247)
IMU: 0 sample [00:00, ? sample/s]2021-07-08 16:09:30,815 - aedat4to2.aedat4to2 - WARNING - IMU sample found: IMU samples will be converted to jAER AEDAT-2.0 assuming full scale 2000 DPS rotation an
d 8g acceleration (aedat4to2.py:256)
IMU: 20167 sample [00:01, 12683.08 sample/s]
2021-07-08 16:09:32,407 - aedat4to2.aedat4to2 - INFO - 20167 IMU samples (aedat4to2.py:271)
sorting: 3656318 ev|imu|fr [00:07, 509197.46 ev|imu|fr/s]
2021-07-08 16:09:42,397 - aedat4to2.aedat4to2 - INFO - F:\tobi\Dropbox (Personal)\GitHub\SensorsINI\aedat4to2\sample1.aedat2 is 1,423,882 kB size, with duration 20.17s, containing 3,635,159 DVS eve
nts at rate 180.2kHz, 141,169 IMU samples, and 992 frames at 49.18Hz (aedat4to2.py:504)
```

You can convert a bunch of files by just supplying them on the command line.

For windows users suffering from cmd.exe limitations, you can start Anaconda Powershell prompt, activate the conda enviroment, and use 
this magic powershell command to process a list of files

````console
(aedat4to2) PS G:\Downloads\1_aedat> aedat4to2.exe $(ls *.aedat4| % {$_.FullName})
2021-07-06 09:30:29,177 - aedat4to2.aedat4to2 - INFO - sensor size width=346 height=260 (aedat4to2.py:140)
2021-07-06 09:30:34,423 - aedat4to2.aedat4to2 - INFO - wrote   3.39e+08 events to alley-2019_11_04_09_36_15.aedat2 (aedat4to2.py:279)
2021-07-06 09:30:34,537 - aedat4to2.aedat4to2 - INFO - sensor size width=346 height=260 (aedat4to2.py:140)
2021-07-06 09:30:39,516 - aedat4to2.aedat4to2 - INFO - wrote   3.26e+08 events to alley-2019_11_04_09_38_03.aedat2 (aedat4to2.py:279)
....


