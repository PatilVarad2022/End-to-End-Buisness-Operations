import yaml
import logging
import os
import sys

def load_config(config_path='config.yaml'):
    # Try to find the config file
    search_paths = [
        config_path,
        os.path.join('..', config_path),
        os.path.join('..', '..', config_path),
        os.path.join(os.getcwd(), config_path)
    ]
    
    found_path = None
    for path in search_paths:
        if os.path.exists(path):
            found_path = path
            break
            
    if not found_path:
        raise FileNotFoundError(f"Config file {config_path} not found in search paths.")
    
    with open(found_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def setup_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to prevent duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
        
    return logger
