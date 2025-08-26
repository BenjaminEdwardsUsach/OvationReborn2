import os
import json
from .convert_to_serializable import convert_to_serializable

def save_cycle_info(info, main_folder, cycle_index):
    """
    Guarda JSON con la info de un ciclo en:
      main_folder/cycle_{cycle_index}/info_{cycle_index}.json
    """
    folder = os.path.join(main_folder, f"cycle_{cycle_index}")
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"info_{cycle_index}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=4, default=convert_to_serializable)
