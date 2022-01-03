# aedat4to2
_aedat4to2_ converts AEDAT4 files from Inivation's [python DV](https://gitlab.com/inivation/dv/dv-python)  into AEDAT-2.0 files for jAER https://github.com/SensorsINI/jaer/. 

Based on inivation AEDAT file format specifications [AEDAT_file_formats](https://inivation.github.io/inivation-docs/Software%20user%20guides/AEDAT_file_formats.html).

Python is required (recommend Anaconda).

Started from useful script https://github.com/bald6354/aedat4tomat .

### Sample of jAER output from converted file from Baldwin DVSMOTION20 dataset
![bike_sample](https://github.com/SensorsINI/aedat4to2/blob/master/sample-jaer-output.png "Sample AEDAT-2.0 output")

# Limitations
_aedat4to2_ now supports DVS events, IMU samples, and APS frames. Please report bugs using issue tracker.

_aedat4to2_ sets the smallest timestamp to be 0 in the output file (to help deal with limitations of int32 timestamp from course int64 timestamp).

## IMU samples
AEDAT-4.0 files encode the IMU values as float physical values.
AEDAT-2.0 encodes the raw IMU ADC values for IMU as 16-bit values; 
see [IMU section in AEDAT-2.0 spec](https://inivation.github.io/inivation-docs/Software%20user%20guides/AEDAT_file_formats.html#bit-30-12). That means it is necessary to set the same values in jAER for playback to result in correct scaling.
The --imu argument sets this scaling; the defaults of 1000 deg/s and 8g may 
not be what you desire. In any case, ensure that in jAER the camera IMU Config in the Hardware Configuration Panel is set correspondingly.


## Installation
Recommended: Make (or use) a conda environment.... maybe it is the same one as dv-python uses.
````shell
conda create --name aedat4to2 python=3.8
conda activate aedat4to2
````

To install directly from git into your activated conda environment
````console
pip install git+https://github.com/SensorsINI/aedat4to2.git
````

Or, from your clone, install on system path to run as aedat4to2. Note the -e that allows your edits to aedata4to2/aedat4to2.py to instantly have effect.
````shell
pip install -e .
````

### Windows DV users
If you have not installed [python DV](https://gitlab.com/inivation/dv/dv-python), you might need to go through one-time installation of
MS visual studio build tools to install [inivation DV software](https://inivation.com/dvp/dvsoftware/) which depends on a package that does not supply pre-built binaries.

See the [inivation python DV docs](https://gitlab.com/inivation/dv/dv-python)

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
Convert a single file, assuming you run within the module folder aedat4to2, using git bash terminal:
```console
$ aedat4to2 aedat4to2/sample1.aedat4
F:\tobi\Dropbox (Personal)\GitHub\SensorsINI\aedat4to2\aedat4to2\sample1.aedat2 exists, overwrite it? [Y/n] y
2021-08-10 09:46:21,349 - aedat4to2.aedat4to2 - INFO - sensor size width=346 height=260 (aedat4to2.py:164)
2021-08-10 09:46:21,729 - aedat4to2.aedat4to2 - INFO - 3635159 DVS events (aedat4to2.py:211)
frames: 992 fr [00:00, 3701.48 fr/s]
2021-08-10 09:46:22,035 - aedat4to2.aedat4to2 - INFO - 992 frames with size (346, 260) (aedat4to2.py:238)
IMU: 0 sample [00:00, ? sample/s]2021-08-10 09:46:22,037 - aedat4to2.aedat4to2 - WARNING - IMU sample found: IMU samples will be converted to jAER AEDAT-2.0 assuming full scale 2000 DPS rotation and 8g acceleration (aedat4to2.py:247)
IMU: 20167 sample [00:01, 12525.64 sample/s]
2021-08-10 09:46:23,646 - aedat4to2.aedat4to2 - INFO - 20167 IMU samples (aedat4to2.py:262)
sorting:   0%|                                                                                                                                                                                                                                | 0/3635159 [00:00<?, ? ev|imu|fr/s]2
021-08-10 09:46:23,769 - aedat4to2.aedat4to2 - INFO - first frame has sample min=185 max=0 mean=77.37438861716316 (aedat4to2.py:474)
sorting: 3656318 ev|imu|fr [00:07, 478722.32 ev|imu|fr/s]
2021-08-10 09:46:34,155 - aedat4to2.aedat4to2 - INFO - F:\tobi\Dropbox (Personal)\GitHub\SensorsINI\aedat4to2\aedat4to2\sample1.aedat2 is 1,423,882 kB size, with duration 20.17s, containing 3,635,159 DVS events at rate 180.2kHz, 141,169 IMU samples at rate 0.9999kHz, and 992
 frames at rate 49.18Hz (aedat4to2.py:503)
```

You can convert one or more files by just supplying them on the command line.

For windows users suffering from cmd.exe limitations, you can start Anaconda Powershell prompt, activate the conda enviroment, and use 
this magic powershell command to process a list of files

````console
(aedat4to2) PS G:\Downloads\1_aedat> aedat4to2.exe $(ls *.aedat4| % {$_.FullName})
2021-07-06 09:30:29,177 - aedat4to2.aedat4to2 - INFO - sensor size width=346 height=260 (aedat4to2.py:140)
2021-07-06 09:30:34,423 - aedat4to2.aedat4to2 - INFO - wrote   3.39e+08 events to alley-2019_11_04_09_36_15.aedat2 (aedat4to2.py:279)
2021-07-06 09:30:34,537 - aedat4to2.aedat4to2 - INFO - sensor size width=346 height=260 (aedat4to2.py:140)
2021-07-06 09:30:39,516 - aedat4to2.aedat4to2 - INFO - wrote   3.26e+08 events to alley-2019_11_04_09_38_03.aedat2 (aedat4to2.py:279)
....


