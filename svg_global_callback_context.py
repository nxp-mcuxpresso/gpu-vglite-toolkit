#
# Copyright 2024 NXP
#
# SPDX-License-Identifier: MIT
#

import sys
import string

# We need to preserve global callback context since APIs are not clearly de-coupled
class GlobalCallbackCtx:

    def _parse_color(self, color_str:str):
        print('Error: Call to dummy parse_color')

    def __init__(self):
        self.parse_color = self._parse_color

    def set_callbacks(self, parse_color):
        self.parse_color = parse_color

CB= GlobalCallbackCtx()

def get_global_callback_context():
    return CB

def update_global_callback_context(parse_color):
    CB.set_callbacks(parse_color)
    return CB
