#!/usr/bin/python


"""
data = {'e_p': e_p,
            'e_ts': e_ts,
            'e_x': e_x,
            'e_y': e_y,
            'f_image': f_image,
            'f_position': f_position,
            'f_size': f_size,
            'f_ts': f_ts,
            'f_framestart': f_framestart,
            'f_frameend': f_frameend,
            'f_expstart': f_expstart,
            'f_expend': f_expend,
            'i_ax': i_ax,
            'i_ay': i_ay,
            'i_az': i_az,
            'i_gx': i_gx,
            'i_gy': i_gy,
            'i_gz': i_gz,
            'i_mx': i_mx,
            'i_my': i_my,
            'i_mz': i_mz,
            'i_temp': i_temp,
            'i_ts': i_ts
           }
"""

import sys, argparse
from dv import AedatFile
import scipy.io as sio
import numpy as np
from numpy import uint32
from tqdm import tqdm
import logging
from pathlib import Path
import \
    struct  # https://stackoverflow.com/questions/846038/convert-a-python-int-into-a-big-endian-string-of-bytes/12859903


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def my_logger(name):
    logger = logging.getLogger(name)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    ch.setFormatter(CustomFormatter())

    logger.addHandler(ch)
    return logger


log = my_logger(__name__)


class Struct:
    pass


def main(argv=None):
    """
    Process command line arguments
    :param argv: list of files to convert, or
    :return:
    """
    if argv is None:
        argv = sys.argv
    inputfile = None
    outputfile = None
    filelist = None
    parser = argparse.ArgumentParser(
        description='Convert files from AEDAT-4 to AEDAT-2 format. Either provide a single -i input_file -o output_file, or a list of .aedat4 input files.')
    parser.add_argument('-o', help='output .aedat2 file name')
    parser.add_argument('-i', help='input .aedat4 file name')
    parser.add_argument('-v', dest='verbose', action='store_true', help='Turn on verbose output')
    args, filelist = parser.parse_known_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    if args.i is not None:
        inputfile = args.i
    if args.o is not None:
        outputfile = args.o

    multiple = outputfile is None

    if inputfile is not None: filelist = [inputfile]

    for file in filelist:
        p = Path(file)
        if not p.exists():
            log.error(f'{p.absolute()} does not exist or is not readable')
            continue
        log.debug(f'loading {file}')
        if multiple:
            p = Path(file)
            outputfile = p.stem + '.aedat2'
        po = Path(outputfile)
        if po.is_file():
            log.error(f'{po.absolute()} exists, will not overwrite')
            continue
        if po.suffix is None or (not po.suffix=='.aedat' and not po.suffix=='.aedat2'):
            log.warning(f'output file {po} does not have .aedat or .aedat2 extension; are you sure this is what you want?')
        with AedatFile(file) as f:  # TODO load entire file to RAM... not ideal
            if f.version != 4:
                log.error(f'AEDAT version must be 4; this file has version {f.version}')
                continue

            height, width = f['events'].size
            log.info(f'sensor size width={width} height={height}')

            # Define output struct
            out = Struct()
            out.data = Struct()
            out.data.dvs = Struct()
            out.data.frame = Struct()
            out.data.imu6 = Struct()

            # Events
            out.data.dvs.polarity = []
            out.data.dvs.timeStamp = []
            out.data.dvs.x = []
            out.data.dvs.y = []

            # Frames
            out.data.frame.samples = []
            out.data.frame.position = []
            out.data.frame.sizeAll = []
            out.data.frame.timeStamp = []
            out.data.frame.frameStart = []
            out.data.frame.frameEnd = []
            out.data.frame.expStart = []
            out.data.frame.expEnd = []

            # IMU
            out.data.imu6.accelX = []
            out.data.imu6.accelY = []
            out.data.imu6.accelZ = []
            out.data.imu6.gyroX = []
            out.data.imu6.gyroY = []
            out.data.imu6.gyroZ = []
            out.data.imu6.temperature = []
            out.data.imu6.timeStamp = []

            data = {'aedat': out}
            # loop through the "events" stream
            log.debug(f'loading events to memory')
            # https://gitlab.com/inivation/dv/dv-python
            events = np.hstack([packet for packet in f['events'].numpy()])  # load events to np array
            out.data.dvs.timeStamp = events['timestamp']  # int64
            out.data.dvs.x = events['x']  # int16
            out.data.dvs.y = events['y']  # int16
            out.data.dvs.polarity = events['polarity']  # int8
            # with tqdm(total=f['events'].size) as pbar:
            #     for e in (f['events']):
            #         out.data.polarity.timeStamp.append(e.timestamp) # TODO convert in RAM entire file, could be better
            #         out.data.polarity.polarity.append(e.polarity)
            #         out.data.polarity.x.append(e.x)
            #         out.data.polarity.y.append(e.y)
            #         pbar.update(1)

            # loop through the "frames" stream
            # log.debug(f'converting frames to RAM')
            # for frame in (f['frames']):
            #     out.data.frame.samples.append(frame.image)
            #     out.data.frame.position.append(frame.position)
            #     out.data.frame.sizeAll.append(frame.size)
            #     out.data.frame.timeStamp.append(frame.timestamp)
            #     out.data.frame.frameStart.append(frame.timestamp_start_of_frame)
            #     out.data.frame.frameEnd.append(frame.timestamp_end_of_frame)
            #     out.data.frame.expStart.append(frame.timestamp_start_of_exposure)
            #     out.data.frame.expEnd.append(frame.timestamp_end_of_exposure)
            #
            # # loop through the "imu" stream
            # log.debug(f'converting IMU samples to RAM')
            # for i in (f['imu']):
            #     a = i.accelerometer
            #     g = i.gyroscope
            #     m = i.magnetometer
            #     out.data.imu6.accelX.append(a[0])
            #     out.data.imu6.accelY.append(a[1])
            #     out.data.imu6.accelZ.append(a[2])
            #     out.data.imu6.gyroX.append(g[0])
            #     out.data.imu6.gyroY.append(g[1])
            #     out.data.imu6.gyroZ.append(g[2])
            #     out.data.imu6.temperature.append(i.temperature)
            #     out.data.imu6.timeStamp.append(i.timestamp)

        # Permute images via numpy
        # tmp = np.transpose(np.squeeze(np.array(out.data.frame.samples)),(1,2,0))
        # out.data.frame.numDiffImages = tmp.shape[2]
        # out.data.frame.size = out.data.frame.sizeAll[0]
        # out.data.frame.samples = tmp.tolist()

        # Add counts
        out.data.dvs.numEvents = len(out.data.dvs.x)
        # out.data.imu6.numEvents = len(out.data.imu6.accelX)


        export_aedat_2(out, outputfile, height=height)

    log.debug('done')

def export_aedat_2(data, filepath, height=260):
    """
    This function exports data to a .aedat file.
    The .aedat file format is documented here:
    http://inilabs.com/support/software/fileformat/

    @param data the data structure from above
    @param filepath the full path to write to, .aedat output file
    @param height the size of the chip, to flip y coordinate for jaer compatibility
    """

    with open(filepath, 'wb') as f:
        # Simple - events only - assume DAVIS
        log.debug(f'saving {filepath}')

        # CRLF \r\n is needed to not break header parsing in jAER
        f.write(b'#!AER-DAT2.0\r\n')
        f.write(b'# This is a raw AE data file created by saveaerdat.m\r\n')
        f.write(b'# Data format is int32 address, int32 timestamp (8 bytes total), repeated for each event\r\n')
        f.write(b'# Timestamps tick is 1 us\r\n')

        # Put the source in NEEDS DOING PROPERLY
        f.write(b'# AEChip: DAVI346\r\n')

        f.write(b'# End of ASCII Header\r\n')

        # DAVIS
        # In the 32-bit address:
        # bit 32 (1-based) being 1 indicates an APS sample
        # bit 11 (1-based) being 1 indicates a special event
        # bits 11 and 32 (1-based) both being zero signals a polarity event

        yShiftBits = 22
        xShiftBits = 12
        polShiftBits = 11
        output = np.zeros([2 * data.data.dvs.numEvents], dtype=uint32)  # allocate horizontal vector to hold output data
        y = np.array((height - 1) - data.data.dvs.y, dtype=uint32) << yShiftBits
        x = np.array(data.data.dvs.x, dtype=uint32) << xShiftBits
        pol = np.array(data.data.dvs.polarity, dtype=uint32) << polShiftBits
        output[
        0::2] = y + x + pol  # clear MSB for DVS event https://inivation.github.io/inivation-docs/Software%20user%20guides/AEDAT_file_formats#bit-31
        output[1::2] = data.data.dvs.timeStamp  # set even elements to timestamps
        bigendian = output.newbyteorder().byteswap(inplace=True)  # Java is big endian, python is little endian
        count = f.write(bigendian) / 2  # write addresses and timestamps, write 4 byte data
        f.close()
        log.info(f'wrote {count:10.3n} events to {filepath}')


if __name__ == "__main__":
    main()
