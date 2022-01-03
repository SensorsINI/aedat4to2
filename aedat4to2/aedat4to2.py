#!/usr/bin/python

"""
aedat4to2 converter main script
Author: Tobi Delbruck
https://github.com/SensorsINI/aedat4to2
"""

import sys, argparse
from dv import AedatFile
import numpy as np
from numpy import uint32, int32, int64, int16
from tqdm import tqdm
import logging
from pathlib import Path
import easygui
import locale

MAX_ADC = 1023
GYRO_FULL_SCALE_DEG_PER_SEC_DEFAULT=1000
ACCEL_FULL_SCALE_M_PER_S_SQ_DEFAULT=8

locale.setlocale(locale.LC_ALL, '') # print numbers with thousands separators

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
    po=None

    parser = argparse.ArgumentParser(
        description='Convert files from AEDAT-4 to AEDAT-2 format. Either provide a single -i input_file -o output_file, or a list of .aedat4 input files.')
    parser.add_argument('-o', help='output .aedat2 file name')
    parser.add_argument('-i', help='input .aedat4 file name')
    parser.add_argument('-q', dest='quiet', action='store_true', help='Turn off all output other than warnings and errors')
    parser.add_argument('-v', dest='verbose', action='store_true', help='Turn on verbose output')
    parser.add_argument('--overwrite', dest='overwrite', action='store_true', help='Overwrite existing output files')
    parser.add_argument('--no_imu', dest='no_imu', action='store_true',
                        help='Do not process IMU samples (which are very slow to extract)')
    parser.add_argument('--imu', nargs='+', type=int, default=[GYRO_FULL_SCALE_DEG_PER_SEC_DEFAULT, ACCEL_FULL_SCALE_M_PER_S_SQ_DEFAULT],
                        help='Use IMU full scale values GYRO ACCEL, e.g. 1000 8 for 1000 deg/s and 8 gravities to encode AEDAT-2.0 values')
    parser.add_argument('--no_frame', dest='no_frame', action='store_true',
                        help='Do not process APS sample frames (which are very slow to extract)')
    args, filelist = parser.parse_known_args() # filelist is list [] of remaining arguments (list of files to be converted)

    if args.verbose:
        log.setLevel(logging.DEBUG)
    elif args.quiet:
        log.setLevel(logging.WARNING)
    else:
        log.setLevel(logging.INFO)

    if len(filelist)==0:
        filelist=easygui.fileopenbox(msg='Select .aedat4 files to convert',
                                      title='aedat4to2',
                                      filetypes=[['*.aedat4','AEDAT-4 files']],
                                      multiple=True,
                                      default='*.aedat4')
        if filelist is None:
            log.info('no file selected, quitting')
            quit(0)
        log.info(f'selected {filelist} with file dialog')
    imu_scale_warning_printed = False

    if args.i is not None:
        inputfile = args.i
    if args.o is not None:
        outputfile = args.o

    multiple = outputfile is None

    imu_scale=args.imu
    if(len(imu_scale)!=2):
        log.error('--imu needs 2 arguments, e.g. --imu 500 2 for 500 deg/s and 2g full scale value encoding')
        quit(1)

    imu_gyro_scale=imu_scale[0]
    imu_accel_scale=imu_scale[1]

    if not imu_gyro_scale in [250,500,1000,2000]:
        log.error(f'--imu gyro scale "{imu_gyro_scale}" not valid, must be one of [250,500,1000,2000]')
        quit(1)

    if not imu_accel_scale in [2,4,8,16]:
        log.error(f'--imu accelerometer scale "{imu_accel_scale}" not valid, must be one of [2,4,8,16]')
        quit(1)

    if inputfile is not None: filelist = [inputfile]

    for file in filelist:
        p = Path(file)
        if not p.exists():
            log.error(f'{p.absolute()} does not exist or is not readable')
            continue
        if p.suffix=='.aedat2':
            log.error(f'skipping AEDAT-2.0 {p.absolute()} as input')
            continue
        log.debug(f'reading input {p}')
        if multiple:
            p = Path(file)

            po = p.with_name(p.stem + '.aedat2') # output is input with .aedat2 extension
        else:
            po = Path(outputfile)
        if not args.overwrite and po.is_file():
            overwrite=query_yes_no(f'{po.absolute()} exists, overwrite it?')
            if not overwrite:
                log.info(f'{po.absolute()} exists, will not overwrite')
                continue
            else:
                try:
                    log.debug(f'overwriting existing {po}')
                    po.unlink()
                except Exception as e:
                    log.error(f'could not delete {po} (maybe it is open in jAER?): {e}')
                    quit(1)
        if po.is_file():
            try:
                with open(outputfile, 'wb') as f:
                    pass
            except IOError as x:
                log.error(f'cannot open {po.absolute()} for output; maybe it is open in jAER?')
                continue
            log.info(f'overwriting {po.absolute()}')
        if po.suffix is None or (not po.suffix == '.aedat' and not po.suffix == '.aedat2'):
            log.warning(
                f'output file {po} does not have .aedat or .aedat2 extension; are you sure this is what you want?')
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
            out.data.frame.samples = [] # np ndarray, [y,x,frame_num], with x=y=0 the UL corner using CV/DV convention
            out.data.frame.position = []
            out.data.frame.sizeAll = []
            out.data.frame.timeStamp = []
            out.data.frame.frameStart = []  # start of readout
            out.data.frame.frameEnd = []  # end of readout
            out.data.frame.expStart = []  # exposure start (before readout)
            out.data.frame.expEnd = []
            out.data.frame.numDiffImages=0
            out.data.frame.size=[]

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

            log.info(f'{len(out.data.dvs.timeStamp)} DVS events')

            def generator():
                while True:
                    yield

            # loop through the "frames" stream
            if not args.no_frame:
                log.debug(f'loading frames to memory')
                with tqdm(generator(), desc='frames', unit=' fr', maxinterval=1) as pbar:
                    for frame in (f['frames']):
                        out.data.frame.samples.append(
                            np.array(frame.image, dtype=np.uint8))  # frame.image is ndarray(h,w,1) with 0-255 values ?? ADC has larger range, maybe clipped
                        out.data.frame.position.append(frame.position)
                        out.data.frame.sizeAll.append(frame.size)
                        out.data.frame.timeStamp.append(frame.timestamp)
                        out.data.frame.frameStart.append(frame.timestamp_start_of_frame)
                        out.data.frame.frameEnd.append(frame.timestamp_end_of_frame)
                        out.data.frame.expStart.append(frame.timestamp_start_of_exposure)
                        out.data.frame.expEnd.append(frame.timestamp_end_of_exposure)
                        pbar.update(1)

                # Permute images via numpy
                tmp = np.transpose(np.squeeze(np.array(out.data.frame.samples)), (1, 2, 0)) # make the frames x,y,frames
                out.data.frame.numDiffImages = tmp.shape[2]
                out.data.frame.size = out.data.frame.sizeAll[0]
                out.data.frame.samples = tmp # leave frames as numpy array
                log.info(f'{out.data.frame.numDiffImages} frames with size {out.data.frame.size}')

            # # loop through the "imu" stream
            if not args.no_imu:
                log.debug(f'loading IMU samples to memory')

                with tqdm(generator(), desc='IMU', unit=' sample') as pbar:
                    for i in (f['imu']):
                        if not imu_scale_warning_printed and imu_gyro_scale==GYRO_FULL_SCALE_DEG_PER_SEC_DEFAULT and imu_accel_scale==ACCEL_FULL_SCALE_M_PER_S_SQ_DEFAULT:
                            log.warning(
                                f'IMU sample found: IMU samples will be converted to jAER AEDAT-2.0 assuming default full scale {GYRO_FULL_SCALE_DEG_PER_SEC_DEFAULT} deg/s rotation and {ACCEL_FULL_SCALE_M_PER_S_SQ_DEFAULT}g acceleration. Use --imu option to change output scaling.')
                            imu_scale_warning_printed = True
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
                log.info(f'{ len(out.data.imu6.accelX)} IMU samples')


    # Add counts of jAER events
        out.data.dvs.numEvents = len(out.data.dvs.x)
        out.data.imu6.numEvents = len(out.data.imu6.accelX) * 7 if not args.no_imu else 0
        out.data.frame.numEvents = (2 * width * height) * (out.data.frame.numDiffImages) if not args.no_frame else 0

        export_aedat_2(args, out, po, height=height)

    log.debug('done')

def export_aedat_2(args, out, filename, height=260, gyro_scale=GYRO_FULL_SCALE_DEG_PER_SEC_DEFAULT, accel_scale=ACCEL_FULL_SCALE_M_PER_S_SQ_DEFAULT):
    """
    This function exports data to a .aedat file.
    The .aedat file format is documented here:
    http://inilabs.com/support/software/fileformat/

    @param out: the data structure from above
    @param filename: the full path to write to, .aedat2 output file
    @param height: the size of the chip, to flip y coordinate for jaer compatibility
    @param gyro_scale: the full scale value of gyro in deg/s
    @param accel_scale: the full scale value of acceleratometer in m/s^2
    """

    num_total_events = out.data.dvs.numEvents + out.data.imu6.numEvents + out.data.frame.numEvents
    printed_stats_first_frame=False


    file_path=Path(filename)
    try:
        f=open(filename, 'wb')
    except IOError as x:
        log.error(f'could not open {file_path.absolute()} for output (maybe opened in jAER already?): {str(x)}')
    else:
        with f:
            # Simple - events only - assume DAVIS
            log.debug(f'saving {file_path.absolute()}')

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

            # see https://inivation.github.io/inivation-docs/Software%20user%20guides/AEDAT_file_formats#bit-31

            apsDvsImuTypeShift=31
            dvsType=0
            apsImuType=1

            imuTypeShift = 28
            imuSampleShift = 12
            imuSampleSubtype = 3
            apsSubTypeShift = 10
            apsAdcShift = 0
            apsResetReadSubtype = 0
            apsSignalReadSubtype = 1

            yShiftBits = 22
            xShiftBits = 12
            polShiftBits = 11




            y = np.array((height - 1) - out.data.dvs.y, dtype=uint32) << yShiftBits
            x = np.array(out.data.dvs.x, dtype=uint32) << xShiftBits
            pol = np.array(out.data.dvs.polarity, dtype=uint32) << polShiftBits
            dvs_addr = (y | x | pol | (dvsType<<apsDvsImuTypeShift)).astype(uint32)  # clear MSB for DVS event https://inivation.github.io/inivation-docs/Software%20user%20guides/AEDAT_file_formats#bit-31
            dvs_timestamps = np.array(out.data.dvs.timeStamp).astype(int64)  # still int64 from DV

            # copied from jAER for IMU sample scaling https://github.com/SensorsINI/jaer/blob/master/src/eu/seebetter/ini/chips/davis/imu/IMUSample.java
            accelSensitivityScaleFactorGPerLsb = 1/8192.
            gyroSensitivityScaleFactorDegPerSecPerLsb = 1/65.5
            temperatureScaleFactorDegCPerLsb = 1/340.
            temperatureOffsetDegC = 35.

            def encode_imu(data, code,  gyro_scale=GYRO_FULL_SCALE_DEG_PER_SEC_DEFAULT, accel_scale=ACCEL_FULL_SCALE_M_PER_S_SQ_DEFAULT):
                """
                Encodes array of IMU data to jAER int32 addresses, assuming https://www.cdiweb.com/datasheets/invensense/ps-mpu-6100a.pdf IMU as used in DAVIS cameras.
                :param data: array of float IMU data
                :param code: the IMU data type code for this array
                :param gyro_scale: the full scale value of gyro in deg/s
                :param accel_scale: the full scale value of acceleratometer in m/s^2

                 :return: the sample AER addressess
                """
                data = np.array(data)  # for speed and operations
                acc_scale=accelSensitivityScaleFactorGPerLsb * (accel_scale/ACCEL_FULL_SCALE_M_PER_S_SQ_DEFAULT)
                if code == 0:  # accelX
                    quantized_data = (-data / acc_scale ).astype(int16)
                elif code == 1 or code == 2:  # acceleration Y,Z
                    quantized_data = (data / acc_scale).astype(int16)
                elif code == 3:  # temperature
                    quantized_data = (data * temperatureScaleFactorDegCPerLsb - temperatureOffsetDegC).astype(int16)
                elif code == 4 : # gyro x
                    # NOTE minus here on yaw, no minus on pitch, to adapt inivation IMU6 type to jaer convention for IMU rotation signs, but no minus for Z (r

                    # jaer encodes the IMU gyro data as
                    # roll (z) positive clockwise facing out from camera
                    # tilt (X) positive tilt up
                    # yaw (or pan) (Y) positive is yaw right

                    # inivation encodes IMU data as float value of actual deg/s.
                    # From [AEDAT_file_formats](https://inivation.github.io/inivation-docs/Software%20user%20guides/AEDAT_file_formats.html)
                    # IMU 6-axes Event
                    # The X, Y and Z axes are referred to the camera plane. X increases to the right, Y going up and Z towards where the lens is pointing. Rotation for the gyroscope is counter-clockwise along the increasing axis, for all three axes.

                    quantized_data = ((data) / (gyroSensitivityScaleFactorDegPerSecPerLsb * (gyro_scale/GYRO_FULL_SCALE_DEG_PER_SEC_DEFAULT)) ).astype(int16)
                elif code == 5 or code == 6: # gyro y,z
                    quantized_data = ((-data) / (gyroSensitivityScaleFactorDegPerSecPerLsb * (gyro_scale/GYRO_FULL_SCALE_DEG_PER_SEC_DEFAULT)) ).astype(int16)
                else:
                    raise ValueError(f'code {code} is not valid')

                encoded_data = ((quantized_data&0xffff) << imuSampleShift) | (code << imuTypeShift) | (imuSampleSubtype << apsSubTypeShift) | (apsImuType<<apsDvsImuTypeShift)
                return encoded_data

            if args.no_imu and args.no_frame: # TODO add frames condition
                all_timestamps=dvs_timestamps
                all_addr=dvs_addr
            else:
                # Make the IMU and frame data into timestamp and encoded AER addr arrays, then
                # sort them together

                # First IMU samples
                imu_addr = np.zeros(out.data.imu6.numEvents, dtype=uint32)
                imu_addr[0::7] = encode_imu(out.data.imu6.accelX, 0)
                imu_addr[1::7] = encode_imu(out.data.imu6.accelY, 1)
                imu_addr[2::7] = encode_imu(out.data.imu6.accelZ, 2)
                imu_addr[3::7] = encode_imu(out.data.imu6.temperature, 3)
                imu_addr[4::7] = encode_imu(out.data.imu6.gyroX, 4)
                imu_addr[5::7] = encode_imu(out.data.imu6.gyroY, 5)
                imu_addr[6::7] = encode_imu(out.data.imu6.gyroZ, 6)

                imu_timestamps = np.empty(out.data.imu6.numEvents, dtype=int64)
                if out.data.imu6.numEvents>0:
                    for i in range(7):
                        imu_timestamps[i::7] = out.data.imu6.timeStamp

                # Now frames
                fr_timestamp=np.array(out.data.frame.timeStamp) # start of frame readout timestamps


                # Now we need to make a single stream of events and timestamps that are monotonic in timestamp order.
                # And we also need to preserve the IMU samples in order 0-6, since AEFileInputStream can only parse them in this order of events.
                # And we need to insert the frame double reset/read samples to the jAER stream
                # That means a slow iteration over all timestamps to take things in order.
                # At least each list of timestamps is in order already
                ldvs = len(dvs_timestamps)
                limu = len(imu_timestamps)
                nfr=len(fr_timestamp)
                hw=(out.data.frame.size) if nfr>0 else (0,0)  # reset and signal samples from DDS readout
                height=hw[1]
                width=hw[0]
                fr_len=height*width # reset + signal samples
                # Add +4 exposure start/end and readout start/end events to total
                tot_len_jaer_events=ldvs+limu+(nfr*(fr_len*2))
                all_timestamps=np.zeros(tot_len_jaer_events,dtype=int64)
                all_addr=np.zeros(tot_len_jaer_events,dtype=uint32)
                max_len=np.max([ldvs, limu,nfr])
                i=0 # overall counter
                id=0 # dvs counter
                ii=0 # imu counter
                ifr=0 # frame counter

                # We need to supply x and y address for every single APS samples in the x and y address fields,
                # And we need to write the APS pixels in in particular order,
                # at least start and end frame with LR and UL corners,
                # since this is how the start and end of each frame is determined by the EventExtractor.

                # jAER uses non-standard computer vision scheme with LL=0,0 and UR=h,w
                # DV uses standard CV scheme of UL=0,0, LR=h,w

                # From Davis346mini.java
                # Inverted with respect to other 346 cameras.
                # setApsFirstPixelReadOut(new Point(getSizeX() - 1, 0)); # start at LR
                # setApsLastPixelReadOut(new Point(0, getSizeY() - 1)); # end at UL

                if nfr>0: # make reset frame to store for each frame
                    aps_xy_addresses=np.zeros([height,width],dtype=uint32)
                    for yy in range(height):
                        for xx in range(width):
                            # fill address fields with APS pixel address
                            # start with xx,yy=0,0 -> width-1,0
                            aps_xy_addresses[yy,xx]=((width-xx-1)<<xShiftBits) | (yy<<yShiftBits)
                    aps_xy_addresses=aps_xy_addresses.flatten()
                    reset_fr= ((MAX_ADC * np.ones(fr_len, dtype=uint32)) << apsAdcShift) | (apsResetReadSubtype << apsSubTypeShift) | (apsImuType << apsDvsImuTypeShift)
                    reset_fr=reset_fr|(aps_xy_addresses)

                with tqdm(total=max_len,unit=' ev|imu|fr',desc='sorting') as pbar:
                    while id< ldvs or ii< limu or ifr<nfr:
                        # if (no IMU or frames) or (no more IMU or frames) or  (no frames and still IMU and dvs < IMU)            or             (no IMU and still frames and dvs<fr) or (DVS < IMU and DVS<fr)
                        if (id<ldvs) and ((limu==0 and nfr==0) or (ii==limu and ifr==nfr) or (nfr==0 and  ii<limu and dvs_timestamps[id]<imu_timestamps[ii]) or (limu==0 and ifr<nfr and dvs_timestamps[id]<fr_timestamp[ifr]) \
                                or (ii==limu or dvs_timestamps[id]<imu_timestamps[ii]) and ( ifr==nfr or dvs_timestamps[id]<fr_timestamp[ifr]) ):
                            # take DVS event
                            all_timestamps[i]=dvs_timestamps[id]
                            all_addr[i]=dvs_addr[id]
                            i+=1
                            id+=1
                        # now we know DVS is later than both IMU and frames, now check if IMU is less than frame time
                        # if (IMU left) and (no more IMU or frames) and ( no frames or IMU < frame)
                        elif (limu>0 and ii<limu) and ( (nfr==0 or ifr==nfr or imu_timestamps[ii]<fr_timestamp[ifr])):
                            # take IMU sample
                            for k in range(7):
                                all_timestamps[i]=imu_timestamps[ii]
                                all_addr[i]=imu_addr[ii]
                                i+=1
                                ii+=1
                        # otherwise it must be frame
                        elif (nfr>0 and ifr<nfr):
                            # take frame
                            all_timestamps[i:i+fr_len*2]=fr_timestamp[ifr] # broadcast all frame samples to same timestamp start of frame readout TODO fix to be frame exposure midpoint
                            fr_samples= MAX_ADC - np.squeeze(out.data.frame.samples[:, :, ifr]) # [y,x,frame_number], DV convention UL=0,0
                            fr_samples=np.flip(fr_samples,0) # flip the y axis (first axis) to match jAER convention
                            fr_vec=fr_samples.flatten().astype(uint32) # frame is flattened so that we start with pixel 0,0 at UL, then go to right across first row, then next row down, etc
                            if not printed_stats_first_frame:
                                printed_stats_first_frame=True
                                min=MAX_ADC-np.min(fr_vec)
                                max=MAX_ADC-np.max(fr_vec)
                                mean=MAX_ADC-np.mean(fr_vec)
                                log.info(f'first frame has sample min={min} max={max} mean={mean}')

                            all_addr[i:i+fr_len]= reset_fr
                            i+=fr_len
                            all_addr[i:i+fr_len]=(aps_xy_addresses) | (fr_vec<<apsAdcShift)|(apsSignalReadSubtype<<apsSubTypeShift)|(apsImuType<<apsDvsImuTypeShift)
                            i+=fr_len
                            ifr+=1

                        pbar.update(1)


            # DV uses int64 timestamps in us, but jaer uses int32, let's subtract the smallest timestamp from everyone
            # that will start the converted recording at time 0
            all_timestamps = all_timestamps - all_timestamps[0]
            all_timestamps = all_timestamps.astype(int32)  # cast to int32...

            output = np.zeros([2 * len(all_addr)], dtype=uint32)  # allocate horizontal vector to hold output data

            output[0::2] = all_addr
            output[1::2] = all_timestamps  # set even elements to timestamps
            bigendian = output.newbyteorder().byteswap(inplace=True)  # Java is big endian, python is little endian
            log.debug(f'writing {len(bigendian)} bytes to {file_path.absolute()}')
            count = f.write(bigendian) / 2  # write addresses and timestamps, write 4 byte data
            f.close()
            max_timestamp=all_timestamps[-1]
            duration=max_timestamp*1e-6
            dvs_rate_khz=ldvs/duration/1000
            frame_rate_hz=nfr/duration
            imu_rate_khz=limu/7/duration/1000 # divide by 7 since each IMU sample is 7 jAER events
            log.info(f'{file_path.absolute()} is {(tot_len_jaer_events*8)>>10:n} kB size, with duration {duration:.4n}s, containing {ldvs:n} DVS events at rate {dvs_rate_khz:.4n}kHz, {limu:n} IMU samples at rate {imu_rate_khz:.4n}kHz, and {nfr:n} frames at rate {frame_rate_hz:.4n}Hz')

# https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input/3041990
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        try:
            choice = input(question + prompt).lower()
            if default is not None and choice == "":
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                print("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n",end=None)
        except KeyboardInterrupt:
            log.info('KeyboardInterrupt, quitting')
            quit(0)


if __name__ == "__main__":
    main()
