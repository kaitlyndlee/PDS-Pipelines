#!/usr/bin/env python

import os
import sys
import subprocess
import logging
import shutil
import argparse
import pvl

from pysis import isis
from pysis.exceptions import ProcessError

from pds_pipelines.config import lock_obj, scratch, pds_log, default_namespace, upc_error_queue
from pds_pipelines.redis_queue import RedisQueue
from pds_pipelines.redis_lock import RedisLock
from pds_pipelines.redis_hash import RedisHash
from pds_pipelines.process import Process
from pds_pipelines.pds_logging import Loggy
from pds_pipelines.pds_process_logging import SubLoggy


def parse_args():
    parser = argparse.ArgumentParser(description='Processing for Projection on the Web')
    parser.add_argument('--key',
                        '-k',
                        dest='key',
                        help='Target key')
    parser.add_argument('--namespace',
                        '-n',
                        dest='namespace',
                        help='Target key')

    args = parser.parse_args()
    return args


def main(user_args):
    key = user_args.key
    namespace = user_args.namespace
    print(namespace)

    if namespace is None:
        namespace = default_namespace

    workarea = scratch + key + '/'
    RQ_file = RedisQueue(key + '_FileQueue', namespace)
    RQ_work = RedisQueue(key + '_WorkQueue', namespace)
    RQ_zip = RedisQueue(key + '_ZIP', namespace)
    RQ_loggy = RedisQueue(key + '_loggy', namespace)
    RQ_final = RedisQueue('FinalQueue', namespace)
    RQ_recipe = RedisQueue(key + '_recipe', namespace)
    RQ_error = RedisQueue(upc_error_queue, namespace)
    RHash = RedisHash(key + '_info')
    RHerror = RedisHash(key + '_error')
    RQ_lock = RedisLock(lock_obj)
    RQ_lock.add({'POW':'1'})

    if int(RQ_file.QueueSize()) == 0:
        print("No Files Found in Redis Queue")
    elif RQ_lock.available('POW'):
        print(RQ_file.getQueueName())
        jobFile = RQ_file.Qfile2Qwork(RQ_file.getQueueName(),
                                      RQ_work.getQueueName())

        # Setup system logging
        basename = os.path.splitext(os.path.basename(jobFile))[0]
        logger = logging.getLogger(key + '.' + basename)
        logger.setLevel(logging.INFO)

        logFileHandle = logging.FileHandler(pds_log + '/Service.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s, %(message)s')
        logFileHandle.setFormatter(formatter)
        logger.addHandler(logFileHandle)

        logger.info('Starting POW Processing')

        # set up loggy
        loggyOBJ = Loggy(basename)


        # File Naming
        if '+' in jobFile:
            bandSplit = jobFile.split('+')
            inputFile = bandSplit[0]
        else:
            inputFile = jobFile

        infile = workarea + \
            os.path.splitext(os.path.basename(jobFile))[0] + '.input.cub'
        outfile = workarea + \
            os.path.splitext(os.path.basename(jobFile))[0] + '.output.cub'


        status = 'success'
        for element in RQ_recipe.RecipeGet():
            if status == 'error':
                break
            elif status == 'success':
                processOBJ = Process()
                process = processOBJ.JSON2Process(element)

                if 'gdal_translate' not in processOBJ.getProcessName():
                    print(processOBJ.getProcessName())
                    if '2isis' in processOBJ.getProcessName():
                        processOBJ.updateParameter('from_', inputFile)
                        processOBJ.updateParameter('to', outfile)
                    elif 'cubeatt-band' in processOBJ.getProcessName():
                        if '+' in jobFile:
                            infileB = infile + '+' + bandSplit[1]
                            processOBJ.updateParameter('from_', infileB)
                            processOBJ.updateParameter('to', outfile)
                            processOBJ.ChangeProcess('cubeatt')
                        else:
                            continue
                    elif 'cubeatt-bit' in processOBJ.getProcessName():
                        if RHash.OutBit() == 'unsignedbyte':
                            temp_outfile = outfile + '+lsb+tile+attached+unsignedbyte+1:254'
                        elif RHash.OutBit() == 'signedword':
                            temp_outfile = outfile + '+lsb+tile+attached+signedword+-32765:32765'
                        processOBJ.updateParameter('from_', infile)
                        processOBJ.updateParameter('to', temp_outfile)
                        processOBJ.ChangeProcess('cubeatt')

                    elif 'spice' in processOBJ.getProcessName():
                        processOBJ.updateParameter('from_', infile)

                    elif 'ctxevenodd' in processOBJ.getProcessName():
                        label = pvl.load(infile)
                        SS = label['IsisCube']['Instrument']['SpatialSumming']
                        print(SS)
                        if SS != 1:
                            continue
                        else:
                            processOBJ.updateParameter('from_', infile)
                            processOBJ.updateParameter('to', outfile)

                    elif 'mocevenodd' in processOBJ.getProcessName():
                        label = pvl.load(infile)
                        CTS = label['IsisCube']['Instrument']['CrosstrackSumming']
                        print(CTS)
                        if CTS != 1:
                            continue
                        else:
                            processOBJ.updateParameter('from_', infile)
                            processOBJ.updateParameter('to', outfile)
                    elif 'mocnoise50' in processOBJ.getProcessName():
                        label = pvl.load(infile)
                        CTS = label['IsisCube']['Instrument']['CrosstrackSumming']
                        if CTS != 1:
                            continue
                        else:
                            processOBJ.updateParameter('from_', infile)
                            processOBJ.updateParameter('to', outfile)
                    elif 'cam2map' in processOBJ.getProcessName():
                        processOBJ.updateParameter('from', infile)
                        processOBJ.updateParameter('to', outfile)

                        if RHash.getGRtype() == 'smart' or RHash.getGRtype() == 'fill':
                            subloggyOBJ = SubLoggy('cam2map')
                            camrangeOUT = workarea + basename + '_camrange.txt'
                            isis.camrange(from_=infile,
                                          to=camrangeOUT)

                            cam = pvl.load(camrangeOUT)

                            if cam['UniversalGroundRange']['MaximumLatitude'] < float(RHash.getMinLat()) or \
                               cam['UniversalGroundRange']['MinimumLatitude'] > float(RHash.getMaxLat()) or \
                               cam['UniversalGroundRange']['MaximumLongitude'] < float(RHash.getMinLon()) or \
                               cam['UniversalGroundRange']['MinimumLongitude'] > float(RHash.getMaxLon()):

                                status = 'error'
                                eSTR = "Error Ground Range Outside Extent Range"
                                RHerror.addError(os.path.splitext(
                                    os.path.basename(jobFile))[0], eSTR)
                                subloggyOBJ.setStatus('ERROR')
                                subloggyOBJ.errorOut(eSTR)
                                loggyOBJ.AddProcess(subloggyOBJ.getSLprocess())
                                break

                            elif RHash.getGRtype() == 'smart':
                                if cam['UniversalGroundRange']['MinimumLatitude'] > float(RHash.getMinLat()):
                                    minlat = cam['UniversalGroundRange']['MinimumLatitude']
                                else:
                                    minlat = RHash.getMinLat()

                                if cam['UniversalGroundRange']['MaximumLatitude'] < float(RHash.getMaxLat()):
                                    maxlat = cam['UniversalGroundRange']['MaximumLatitude']
                                else:
                                    maxlat = RHash.getMaxLat()

                                if cam['UniversalGroundRange']['MinimumLongitude'] > float(RHash.getMinLon()):
                                    minlon = cam['UniversalGroundRange']['MinimumLongitude']
                                else:
                                    minlon = RHash.getMinLon()

                                if cam['UniversalGroundRange']['MaximumLongitude'] < float(RHash.getMaxLon()):
                                    maxlon = cam['UniversalGroundRange']['MaximumLongitude']
                                else:
                                    maxlon = RHash.getMaxLon()
                            elif RHash.getGRtype() == 'fill':
                                minlat = RHash.getMinLat()
                                maxlat = RHash.getMaxLat()
                                minlon = RHash.getMinLon()
                                maxlon = RHash.getMaxLon()

                            processOBJ.AddParameter('minlat', minlat)
                            processOBJ.AddParameter('maxlat', maxlat)
                            processOBJ.AddParameter('minlon', minlon)
                            processOBJ.AddParameter('maxlon', maxlon)

                            #os.remove(camrangeOUT)

                    elif 'isis2pds' in processOBJ.getProcessName():
                        finalfile = infile.replace('.input.cub', '_final.img')
                        processOBJ.updateParameter('from_', infile)
                        processOBJ.updateParameter('to', finalfile)

                    else:
                        processOBJ.updateParameter('from_', infile)
                        processOBJ.updateParameter('to', outfile)

                    print(processOBJ.getProcess())

                    for k, v in processOBJ.getProcess().items():
                        func = getattr(isis, k)
                        subloggyOBJ = SubLoggy(k)
                        try:
                            func(**v)
                            logger.info('Process %s :: Success', k)
                            subloggyOBJ.setStatus('SUCCESS')
                            subloggyOBJ.setCommand(processOBJ.LogCommandline())
                            subloggyOBJ.setHelpLink(processOBJ.LogHelpLink())
                            loggyOBJ.AddProcess(subloggyOBJ.getSLprocess())

                            if os.path.isfile(outfile):
                                os.rename(outfile, infile)
                            status = 'success'

                        except ProcessError as e:
                            RQ_error.QueueAdd(f'Process {k} failed for {jobFile}')
                            logger.error('Process %s :: Error', k)
                            logger.error(e)
                            status = 'error'
                            eSTR = 'Error Executing ' + k + \
                                ' Standard Error: ' + str(e)
                            RHerror.addError(os.path.splitext(
                                os.path.basename(jobFile))[0], eSTR)
                            subloggyOBJ.setStatus('ERROR')
                            subloggyOBJ.setCommand(processOBJ.LogCommandline())
                            subloggyOBJ.setHelpLink(processOBJ.LogHelpLink())
                            subloggyOBJ.errorOut(eSTR)
                            loggyOBJ.AddProcess(subloggyOBJ.getSLprocess())
                            RQ_work.QueueRemove(jobFile)
                            break

                else:
                    GDALcmd = ""
                    for process, v, in processOBJ.getProcess().items():
                        subloggyOBJ = SubLoggy(process)
                        GDALcmd += process
                        for dict_key, value in v.items():
                            GDALcmd += ' ' + dict_key + ' ' + value

                    frmt = RHash.Format()
                    if frmt == 'GeoTiff-BigTiff':
                        fileext = 'tif'
                    elif frmt == 'GeoJPEG-2000':
                        fileext = 'jp2'
                    elif frmt == 'JPEG':
                        fileext = 'jpg'
                    elif frmt == 'PNG':
                        fileext = 'png'
                    elif frmt == 'GIF':
                        fileext = 'gif'

                    logGDALcmd = GDALcmd + ' ' + basename + \
                        '.input.cub ' + basename + '_final.' + fileext
                    finalfile = infile.replace(
                        '.input.cub', '_final.' + fileext)
                    GDALcmd += ' ' + infile + ' ' + finalfile
                    print(GDALcmd)

                    result = subprocess.call(GDALcmd, shell=True)
                    if result == 0:
                        logger.info('Process GDAL translate :: Success')
                        status = 'success'
                        subloggyOBJ.setStatus('SUCCESS')
                        subloggyOBJ.setCommand(logGDALcmd)
                        subloggyOBJ.setHelpLink(
                            'http://www.gdal.org/gdal_translate.html')
                        loggyOBJ.AddProcess(subloggyOBJ.getSLprocess())
                        #os.remove(infile)
                    else:
                        errmsg = 'Error Executing GDAL translate: Error'
                        logger.error(errmsg)
                        status = 'error'
                        RHerror.addError(os.path.splitext(
                            os.path.basename(jobFile))[0], errmsg)
                        subloggyOBJ.setStatus('ERROR')
                        subloggyOBJ.setCommand(logGDALcmd)
                        subloggyOBJ.setHelpLink(
                            'http://www.gdal.org/gdal_translate.html')
                        subloggyOBJ.errorOut('Process GDAL translate :: Error')
                        loggyOBJ.AddProcess(subloggyOBJ.getSLprocess())

        if status == 'success':

            if RHash.Format() == 'ISIS3':
                finalfile = infile.replace('.input.cub', '_final.cub')
                shutil.move(infile, finalfile)
            if RHash.getStatus() != 'ERROR':
                RHash.Status('SUCCESS')

            try:
                RQ_zip.QueueAdd(finalfile)
                logger.info('File Added to ZIP Queue')
            except:
                logger.error('File NOT Added to ZIP Queue')

        elif status == 'error':
            RHash.Status('ERROR')
            if os.path.isfile(infile):
                #os.remove(infile)
                pass

        try:
            RQ_loggy.QueueAdd(loggyOBJ.Loggy2json())
            RQ_work.QueueRemove(jobFile)
            logger.info('JSON Added to Loggy Queue')
        except:
            logger.error('JSON NOT Added to Loggy Queue')

        if RQ_file.QueueSize() == 0 and RQ_work.QueueSize() == 0:
            try:
                RQ_final.QueueAdd(key)
                logger.info('Key %s Added to Final Queue: Success', key)
                logger.info('Both Queues Empty: filequeue = %s  work queue = %s', str(
                    RQ_file.QueueSize()), str(RQ_work.QueueSize()))
                logger.info('JOB Complete')
            except:
                logger.error('Key NOT Added to Final Queue')
        elif RQ_file.QueueSize() == 0 and RQ_work.QueueSize() != 0:
            logger.warning('Work Queue Not Empty: filequeue = %s  work queue = %s', str(
                RQ_file.QueueSize()), str(RQ_work.QueueSize()))


if __name__ == "__main__":
    sys.exit(main(parse_args()))
