# aedat4to2
Convert AEDAT4 files from Inivation's DV https://gitlab.com/inivation/dv/dv-python into AEDAT-2.0 files for jAER https://github.com/SensorsINI/jaer/. 

Based on AEDAT file format specifications in https://inivation.github.io/inivation-docs/Software%20user%20guides/AEDAT_file_formats.html

Python is required (recommend Anaconda).

Started from useful script https://github.com/bald6354/aedat4tomat

## Installation
Recommended: Make a conda environment....
````shell
conda create --name aedat4to2 python=3.8
conda activate aedat4to2
````


Install on system path to run as aedat4to2. Note the -e that allows your edits to aedat4to2.py to instantly have effect
````shell
pip install -e .
````

## If you just want to develop and not install.

Install the dv module...
```
pip install dv
```

Install the requirements....
````shell
pip install -r requirements.txt
````


# Example Conversion:
Convert a single file
```console
foo@bar:~$ python /home/username/aedat4to2.py -i "dvFile.aedat4" -o "dvFile.aedat"
```

Convert a bunch of files from .aedat4 to .aedat2 (assuming you have installed aedat4to2)
````console
aedat4to2 *.aedat4
````

# Limitations
This code only writes DVS brightness change events from with aedat4 files for now. Pls request IMU samples and frames.
