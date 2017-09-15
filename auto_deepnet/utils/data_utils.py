from __future__ import absolute_import, division, print_function
import sys
import os
curr_path = os.path.abspath(os.path.dirname(__file__))
sys.path = [os.path.dirname(os.path.dirname(curr_path)), curr_path] + sys.path
curr_path = None
try:
    import cPickle as pickle
except:
    import pickle
import logging
import csv
import h5py
import numpy as np
import pandas as pd
import re
import auto_deepnet.utils.exceptions as exceptions

logger = logging.getLogger("auto_deepnet")
logger.setLevel(logging.DEBUG)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


'''
function: save_pickle_data
inputs:
    - file_path: string pathname to save data to
    - dataFrame: pandas dataFrame to save to disk in any picklable format
    - pandas_format: whether to save as a pandas dataframe or as a numpy array
description:
    helper function to save any data to disk via pickling
'''
def save_pickle_data(file_path, dataFrame, pandas_format=True, **kwargs):
    logger.info("Pickling and writing to disk...")
    try:
        if pandas_format:
            dataFrame.to_pickle(file_path)
        else:
            with open(file_path, 'wb') as f:
                pickle.dump(dataFrame.values)
    except Exception as e:
        logger.exception("Failed with Error {0}".format(e))
        raise exceptions.FileSaveError
    logger.info("Successfully pickled and saved file")


'''
function: load_pickle_data
inputs:
    - file_path: string pathname to load data from
    - pandas_format (optional): whether the pickled data is a pandas dataFrame
description:
    helper function to load any pickled data from disk
'''
def load_pickle_data(file_path, pandas_format=True, **kwargs):
    logger.info("Opening file to read and unpickle...")
    try:
        if pandas_format:
            data = pd.read_pickle(file_path)
        else:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
    except Exception as e:
        logger.exception("Failed with Error {0}".format(e))
        raise exceptions.FileLoadError
    logger.info("Successfully read and unpickled file")
    return data


'''
function: save_hdf5_data
inputs:
    - file_path: string pathname to save data to
    - dataFrame: the pandas dataframe to save to disk
    - pandas_format (optional): whether to save as a pandas structure or default hdf5
    - mode (optional): The mode to open file as
    - key (optional): The name to call the dataset
    - append (optional): Whether data should be appended or replaced
'''
def save_hdf5_data(file_path, dataFrame, pandas_format=True, mode='a', key=None, append=False, **kwargs):
    logger.info("Writing HDF5 to disk...")
    try:
        if pandas_format:
            with pd.HDFStore(file_path, mode=mode) as f:
                f.put(key=key, value=dataFrame, append=append, **kwargs)
        else:
            if key == None:
                logger.error("Need a key when saving as default HDF5 format")
                raise exceptions.FileSaveError
            with h5py.File(file_path, mode) as f:
                if key in f:
                    del f[key]
                f.create_dataset(key, data=dataFrame.values)
    except Exception as e:
        logger.exception("Failed with Error {0}".format(e))
        raise exceptions.FileSaveError
    logger.info("Successfully saved hdf5 data")


'''
function: load_hdf5_file
inputs:
    - file_path: string pathname to load data from
    - read_only (optional): whether to load file as a read only file
    - pandas_format (optional): whether the file was saved in pandas format
    - key (optional): name of the dataset
description:
    helper function to load an hdf5 file from disk
'''
def load_hdf5_data(file_path, read_only=True, pandas_format=True, key=None, **kwargs):
    if not file_path:
        logger.error("Invalid file path")
        raise exceptions.FileLoadError("Invalid file path")
    logger.info("Attempting to open HDF5 File from {}...".format(file_path))
    mode = 'r' if read_only else 'a'
    if not os.path.isfile(file_path):
        if read_only:
            logger.error("File {} does not exist".format(file_path))
            raise exceptions.FileLoadError("File does not exist")
        logger.info("File {} does not exist. Creating...".format(file_path))
    else:
        logger.info("Opening File {}...".format(file_path))
    if pandas_format:
        return pd.read_hdf(file_path, key=key, mode=mode, **kwargs)
    else:
        with h5py.File(file_path, mode) as f:
            try:
                data = f[key][()]
            except KeyError as e:
                logger.exception("Dataset {} does not exist".format(dataset))
                raise exceptions.FileLoadError("Dataset does not exist")
            except Exception as e:
                logger.exception("Problem loading dataset: {0}".format(e))
                raise exceptions.FileLoadError
        return data


##TODO##
def save_csv_data(file_path, dataFrame, **kwargs):
    pass


'''
function: load_csv_data
inputs:
    - file_path: string pathname to load data from
    - header (optional): whether there is a header in the csv file
    - dtype (optional): the data format
    - converters (optional): converters for any columns
    - skiprows (optional): lines to skip
'''
def load_csv_data(file_path, header='infer', dtype=np.float32, converters=None, skiprows=None):
    if not (file_path or os.path.isfile(file_path)):
        logger.error("Invalid file path")
        raise exceptions.FileLoadError("Invalid file path")
    logger.info("Loading CSV data from {}...".format(file_path))
    try:
        data = pd.read_csv(file_path, header=header, dtype=dtype, converters=converters, skiprows=skiprows)
    except Exception as e:
        logger.exception("Problem reading CSV: {0}".format(e))
        raise exceptiions.FileSaveError
    logger.info("Successfully loaded CSV data")
    return data


'''
function: save_data
inputs:
    - file_path: string pathname to save data to
    - dataFrame: data to save to disk
    - pandas_format (optional): whether to save as a pandas dataframe or as a numpy array
    - mode (optional): mode to open file in
    - format (optional): format to save to disk
'''
def save_data(file_path, dataFrame, pandas_format=True, mode='a', format='hdf5', **kwargs):
    logger.info("Attempting to save data to {}...".format(file_path))
    try:
        dir_name, file_name = os.path.split(file_path)
    except Exception as e:
        logger.exception("Error with file path {}: {}".format(file_path, e))
        raise exceptions.FileSaveError("Invalid file path")
    if not os.path.isdir(dir_name):
        logger.info("Directory {} does not exist. Creating...".format(dir_name))
        os.makedirs(dir_name)
    if os.path.isfile(file_path) and (mode == 'w' or format == 'pickle'):
        logger.warning("File {} will be overwritten".format(file_path))
        os.remove(file_path)
    
    saver = {
        'hdf5': save_hdf5_data,
        'csv': save_csv_data,
        'pickle': save_pickle_data
    }
    try:
        saver.get(format, save_hdf5_data)(file_path, dataFrame, pandas_format, mode, **kwargs)
    except Exception as e:
        logger.exceptions("Error saving file {}".format(file_path))
        raise exceptions.FileSaveError
