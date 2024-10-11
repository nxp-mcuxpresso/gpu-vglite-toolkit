import sys
import string

# We need to preserve global callback context since APIs are not clearly de-coupled
class GlobalCallbackCtx:

    def _parse_color(self, color_str:str):
        print('Error: Call to dummy parse_color')
        pass

    def _get_current_unique_id(self):
        print('Error: Call to dummy def get_current_unique_id()')
        pass

    def _get_input_file_cname(self):
        print('Error: Call to dummy get_input_file_cname')
        pass

    def __init__(self):
        self.parse_color = self._parse_color
        self.get_current_unique_id = self._get_current_unique_id
        self.get_input_file_cname = self._get_input_file_cname

    def set_callbacks(self, parse_color, get_current_unique_id, get_input_file_cname):
        self.parse_color = parse_color
        self.get_current_unique_id = get_current_unique_id
        self.get_input_file_cname = get_input_file_cname

CB= GlobalCallbackCtx()

def get_global_callback_context():
    return CB

def update_global_callback_context(parse_color, get_current_unique_id, get_input_file_cname):
    CB.set_callbacks(parse_color, get_current_unique_id, get_input_file_cname)
    return CB
