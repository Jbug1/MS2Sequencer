#Sequence Spectra
from logging import getLogger, basicConfig
from importlib.util import spec_from_file_location, module_from_spec
import shutil
from os import makedirs
from MS2sequencer import deltaSolver, parentFormula
import pandas as pd
from joblib import Parallel, delayed


def main(config_path):

    module_spec = spec_from_file_location('config', config_path)
    config = module_from_spec(module_spec)
    module_spec.loader.exec_module(config)

    makedirs(config.log_path, exist_ok = True)
    basicConfig(filename = f'{config.log_path}/training_log.log', 
                level = "INFO", format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    logger = getLogger(__name__)

    #copy config file to log folder
    shutil.copy(config_path, f'{config.log_path}/config.py')

    logger.info(f'instantiated log and copied config')

    #read inputs to be sequenced
    input_data = pd.read_pickle(config.pickle_path)

    filtered_spectra = Parallel(n_jobs = config.jobs)(delayed(deltaSolver.filter_spec)(spectrum, config.min_intensity_pct) 
                                                      for spectrum in input_data['spectrum'].tolist())

    sequence_outputs = Parallel(n_jobs = config.jobs)(delayed(deltaSolver.sequence_spectrum)(spectrum = spectrum, 
                                                                                             elements = config.elements,
                                                                                             element_limits = config.element_limits,
                                                                                             max_start_mz = config.max_start_mz,
                                                                                             beam_width = config.beam_width
                                                                                             ) 
                                                      for spectrum in filtered_spectra)
    
    sequence_outputs_annotated = Parallel(n_jobs = config.jobs)(delayed(deltaSolver.annotate_results)(element)
                                                                for element in sequence_outputs)

    
    

