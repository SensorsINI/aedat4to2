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
import numpy as np
from numpy import uint32, int32
from tqdm import tqdm
import logging
from pathlib import Path
import struct  # https://stackoverflow.com/questions/846038/convert-a-python-int-into-a-big-endian-string-of-bytes/12859903


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
    parser.add_argument('--overwrite', dest='overwrite', action='store_true', help='Overwrite existing output files')
    parser.add_argument('--no_imu', dest='no_imu', action='store_true', help='Do not process IMU samples (which are very slow to extract)')
    parser.add_argument('--no_frame', dest='no_frame', action='store_true', help='Do not process APS sample frames (which are very slow to extract)')
    args, filelist = parser.parse_known_args()

    imu_scale_warning_printed=False

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
        if not args.overwrite and po.is_file():
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
            out.data.frame.frameStart = [] # start of readout
            out.data.frame.frameEnd = [] # end of readout
            out.data.frame.expStart = [] # exposure start (before readout)
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
            #         out.data.polarity.timeStamp.append(e.timestamp)
            #         out.data.polarity.polarity.append(e.polarity)
            #         out.data.polarity.x.append(e.x)
            #         out.data.polarity.y.append(e.y)
            #         pbar.update(1)

            def generator():
                while True:
                    yield

            # loop through the "frames" stream
            if not args.no_frame:
                log.debug(f'loading frames to memory')
                with tqdm(generator(),desc='frames',unit=' fr') as pbar:
                    for frame in (f['frames']):
                        out.data.frame.samples.append(frame.image) #  frame.image is ndarray(h,w,1) with 0-255 values ?? ADC has larger range, maybe clipped
                        out.data.frame.position.append(frame.position)
                        out.data.frame.sizeAll.append(frame.size)
                        out.data.frame.timeStamp.append(frame.timestamp)
                        out.data.frame.frameStart.append(frame.timestamp_start_of_frame)
                        out.data.frame.frameEnd.append(frame.timestamp_end_of_frame)
                        out.data.frame.expStart.append(frame.timestamp_start_of_exposure)
                        out.data.frame.expEnd.append(frame.timestamp_end_of_exposure)
                        pbar.update(1)

                # Permute images via numpy
                tmp = np.transpose(np.squeeze(np.array(out.data.frame.samples)),(1,2,0))
                out.data.frame.numDiffImages = tmp.shape[2]
                out.data.frame.size = out.data.frame.sizeAll[0]
                out.data.frame.samples = tmp.tolist()


            # # loop through the "imu" stream
            if not args.no_imu:
                log.debug(f'loading IMU samples to memory')

                with tqdm(generator(),desc='IMU',unit=' sample') as pbar:
                    for i in (f['imu']):
                        if not imu_scale_warning_printed:
                            log.warning(f'IMU sample found: IMU samples will be converted to jAER AEDAT-2.0 assuming full scale 2000 DPS rotation and 8g acceleration')
                            imu_scale_warning_printed=True
                        a = i.accelerometer
                        g = i.gyroscope
                        m = i.magnetometer
                        out.data.imu6.accelX.append(a[0])
                        out.data.imu6.accelY.append(a[1])
                        out.data.imu6.accelZ.append(a[2])
                        out.data.imu6.gyroX.append(g[0])
                        out.data.imu6.gyroY.append(g[1])
                        out.data.imu6.gyroZ.append(g[2])
                        out.data.imu6.temperature.append(i.temperature)
                        out.data.imu6.timeStamp.append(i.timestamp)
                        pbar.update(1)



        # Add counts
        out.data.dvs.numEvents = len(out.data.dvs.x)
        out.data.imu6.numEvents = len(out.data.imu6.accelX)*7 if not args.no_imu else 0
        out.data.frame.numEvents = (4+2*width*height)*(out.data.frame.numDiffImages) if not args.no_frame else 0


        export_aedat_2(out, outputfile, height=height)

    log.debug('done')

def export_aedat_2(out, filepath, height=260):
    """
    This function exports data to a .aedat file.
    The .aedat file format is documented here:
    http://inilabs.com/support/software/fileformat/

    @param out the data structure from above
    @param filepath the full path to write to, .aedat output file
    @param height the size of the chip, to flip y coordinate for jaer compatibility
    """


    num_total_events= out.data.dvs.numEvents + out.data.imu6.numEvents+out.data.frame.numEvents

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
        output = np.zeros([2 * out.data.dvs.numEvents], dtype=uint32)  # allocate horizontal vector to hold output data
        y = np.array((height - 1) - out.data.dvs.y, dtype=uint32) << yShiftBits
        x = np.array(out.data.dvs.x, dtype=uint32) << xShiftBits
        pol = np.array(out.data.dvs.polarity, dtype=uint32) << polShiftBits
        dvs_addr = (y + x + pol).astype(uint32)  # clear MSB for DVS event https://inivation.github.io/inivation-docs/Software%20user%20guides/AEDAT_file_formats#bit-31
        dvs_timestamps = np.array(out.data.dvs.timeStamp).astype(int32)  # set even elements to timestamps

        imuTypeShift=27
        imuSampleShift=11
        imuSampleSubtype=3
        apsSubTypeShift=9
        apsAdcShift=0
        apsResetReadSubtype=0
        apsSignalReadSubtype=1

        # copied from jAER for IMU sample scaling https://github.com/SensorsINI/jaer/blob/master/src/eu/seebetter/ini/chips/davis/imu/IMUSample.java
        accelSensitivityScaleFactorGPerLsb = 8192
        gyroSensitivityScaleFactorDegPerSecPerLsb =  65.5
        temperatureScaleFactorDegCPerLsb = 340
        temperatureOffsetDegC = 35
        def encode_imu(data,code):
            data=np.array(data) # for speed and operations
            if code==0: # accelX
                encoded_data=(-data*accelSensitivityScaleFactorGPerLsb).astype(int32)
            elif code==1 or code==2: # acceleration Y,Z
                encoded_data=(data*accelSensitivityScaleFactorGPerLsb).astype(int32)
            elif code==3: #temperature
                encoded_data=(data*temperatureScaleFactorDegCPerLsb-temperatureOffsetDegC).astype(int32)
            elif code==4 or code==5 or code==6:
                encoded_data=(data*gyroSensitivityScaleFactorDegPerSecPerLsb).astype(int32)
            else:
                raise ValueError(f'code {code} is not valid' )

            encoded_data=encoded_data<<imuSampleShift+code<<imuTypeShift+imuSampleSubtype<<apsSubTypeShift
            return encoded_data

        imuData=np.zeros(out.data.imu6.numEvents,dtype=int32)
        imuData[0::7]=encode_imu(out.data.imu6.accelX,0)
        imuData[1::7]=encode_imu(out.data.imu6.accelY,1)
        imuData[2::7]=encode_imu(out.data.imu6.accelZ,2)
        imuData[3::7]=encode_imu(out.data.imu6.temperature,3)
        imuData[4::7]=encode_imu(out.data.imu6.gyroX,4)
        imuData[5::7]=encode_imu(out.data.imu6.gyroY,5)
        imuData[6::7]=encode_imu(out.data.imu6.gyroZ,6)

        imuTimestamps=np.empty(out.data.imu6.numEvents)
        for i in range(7):
            imuTimestamps[i::7]=out.data.imu6.timeStamp

        output[0::2] = dvs_addr  # clear MSB for DVS event https://inivation.github.io/inivation-docs/Software%20user%20guides/AEDAT_file_formats#bit-31
        output[1::2] = dvs_timestamps  # set even elements to timestamps
        bigendian = output.newbyteorder().byteswap(inplace=True)  # Java is big endian, python is little endian
        count = f.write(bigendian) / 2  # write addresses and timestamps, write 4 byte data
        f.close()
        log.info(f'wrote {count:10.3n} events to {filepath}')


if __name__ == "__main__":
    main()
