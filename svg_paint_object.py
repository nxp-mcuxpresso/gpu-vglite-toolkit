import sys

# Import application specific routines
from svg_colors import SVG_DEFAULT_BLACK_COLOR
from svg_global_callback_context import *

CB = get_global_callback_context()

def get_min_max_coordinates(parsed_lines):
    min_x = min(coord[0] for coord in parsed_lines)
    max_x = max(coord[0] for coord in parsed_lines)
    min_y = min(coord[1] for coord in parsed_lines)
    max_y = max(coord[1] for coord in parsed_lines)
    return min_x, max_x, min_y, max_y

class SolidColor:
    def __init__(self, color_str):
        self.set_color(color_str)    

    def set_color(self, color_str):
        self.color = color_str
    
class GradientStopPoints:
    def __init__(self, offset, hex_color_str):
        self.offset = offset
        self.color_str = hex_color_str

class GradientBase:
    def __init__(self):
        self._valid:bool = False
        self.name = None
        self.grad_index = -1

    def is_valid(self):
        return self._valid

    def set_name(self, name):
        self.name = name
    
    def set_index(self, index):
        self.grad_index = index

    def convert_offset(self, offset):
        if offset.endswith('%'):
            return float(offset.strip('%')) / 100.0
        return float(offset)

    def _get_stop_color(self, stop):
        global CB

        hex_color = "0x%x" % 0xff000000
        offset = 0.0
        if 'offset' in stop:
            offset = self.convert_offset(stop['offset'])
        if 'stop-color' in stop:
            name = stop['stop-color']
            stop_color, isSolidColor2 = CB.parse_color(name)
            if stop_color :
                hex_color = stop_color
            else:
                print("Error: stop color value not supported", sep="---",file=sys.stderr)
        return hex_color, offset

    def _parse_gradient_stop_points(self, alist):
        grad_stops:list[GradientStopPoints] = []
        for stop in alist['stops']:
            hex_color, offset = self._get_stop_color(stop)
            grad_stops.append(GradientStopPoints(offset, hex_color))

        return grad_stops

    def _stops_to_string(self, prefix, stops):
        """
        Create necesary datastructure for stop points
        """
        # local variables
        str_buf = ''
        
        str_buf = f"static stopValue_t {prefix}[] = {{\n"
        for s in stops:
                str_buf += f"    {{ .offset = {s.offset}, .stop_color = {s.color_str} }},\n"
        # C compiler gives error if there is comma (,) in array
        # So from str_buf we are removing ,\n
        str_buf = str_buf[:-2]
        str_buf += "\n};\n\n\n"
        return str_buf

class LinearGradient(GradientBase):
    """
    A class to parse radial gradient data from SVG context
    and prepare VGLite draw commands
    """
    def __init__(self):
        self._valid:bool = False
        self.name = None
        self.grad_index = -1
        self.stops: list[GradientStopPoints] = []

    def get_fill_mode(self):
        if len(self.stops) > 0:
            return "FILL_LINEAR_GRAD"
        else:
            # As per the SVG spec (https://www.w3.org/TR/SVG2/paths.html#PathDataMovetoCommands)
            # If no stops are defined, then painting shall occur as if 'none' were specified as the paint style.
            return "STROKE"
    
    def parse(self, alist, data_str):
        self.stops = self._parse_gradient_stop_points(alist)
        if len(self.stops) == 0:
            self._valid = False
            return

        grad_unit_str = alist['gradientUnits']
        min_x, max_x, min_y, max_y = get_min_max_coordinates(data_str)
        x1 = y1 = x2 = y2 = 0.0
        if grad_unit_str == 'userSpaceOnUse':
            x1 = float(alist['x1'])
            y1 = float(alist['y1'])
            x2 = float(alist['x2'])
            y2 = float(alist['y2'])
        elif grad_unit_str == 'objectBoundingBox':
            x1 = min_x + (((max_x - min_x) * float(alist['x1'])) if 'x1' in alist else 0 )
            y1 = min_y + (((max_y - min_y) * float(alist['y1'])) if 'y1' in alist else 0 )
            x2 = min_x + (((max_x - min_x) * float(alist['x2'])) if 'x2' in alist else 0 )
            y2 = min_y + (((max_y - min_y) * float(alist['y2'])) if 'y2' in alist else 0 )
        else:
            x1 = min_x
            y1 = min_y
            x2 = max_x
            y2 = max_y
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        # Finally mark gradient as valid
        self._valid = True

    def to_string(self):
        # local variables
        str_buf = ''
        if len(self.stops) == 0 or self.is_valid == False:
            return str_buf

        prefix = f"linearGrad_{CB.get_current_unique_id()}"
        str_buf = self._stops_to_string(prefix,self.stops)

        str_buf += f"static linearGradient_t {CB.get_input_file_cname()}_linear_gradients_{self.grad_index}[] = {{\n"
        str_buf += f"    {{\n"
        str_buf += f"        /*grad id={self.name}*/\n"
        str_buf += f"        .num_stop_points = {len(self.stops)},\n"
        str_buf += f"        .linear_gradient = {{{self.x1}f, {self.y1}f, {self.x2}f, {self.y2}f}},\n"
        str_buf += f"        .stops = {prefix}\n"
        str_buf += f"    }},\n"
        str_buf += "\n};\n\n"
        return str_buf


class RadialGradient(GradientBase):
    """
    A class to parse radial gradient data from SVG context
    and prepare VGLite draw commands
    """
    def __init__(self):
        self._valid:bool = False
        self.name = None
        self.grad_index = -1
        self.stops: list[GradientStopPoints] = []
        self.cx = 0.0
        self.cy = 0.0
        self.r = 0.0
        self.fx= 0.0
        self.fy= 0.0
    

    def get_fill_mode(self):
        if len(self.stops) > 0:
            return "FILL_RADIAL_GRAD"
        else:
            return "STROKE"
    
    def parse(self, alist, data_str):        
        self.stops = self._parse_gradient_stop_points(alist)
        if len(self.stops) == 0:
            return

        grad_unit_str = alist['gradientUnits']
        min_x, max_x, min_y, max_y = get_min_max_coordinates(data_str)
        if grad_unit_str == 'userSpaceOnUse':
                cx = float(alist['cx'])
                cy = float(alist['cy'])
                r  = float(alist['r'])
                fx = float(alist['cx'])
                fy = float(alist['cy'])
        elif grad_unit_str == None or grad_unit_str == 'objectBoundingBox':
            if all(key in alist for key in ('cx', 'cy', 'r', 'fx', 'fy')):
                cx = min_x + (max_x - min_x) * self.convert_offset(alist['cx'])
                cy = min_y + (max_y - min_y) * self.convert_offset(alist['cy'])
                r = min(min_x + (max_x - min_x) * self.convert_offset(alist['r']),
                            min_y + (max_y - min_y) * self.convert_offset(alist['r']))
                fx = min_x + (max_x - min_x) * self.convert_offset(alist['fx'])
                fy = min_y + (max_y - min_y) * self.convert_offset(alist['fy'])
            #cx, cy and r gradient parameters are available but fx and fy is missing
            if all(key in alist for key in ('cx', 'cy', 'r')):
                cx = min_x + (max_x - min_x) * self.convert_offset(alist['cx'])
                cy = min_y + (max_y - min_y) * self.convert_offset(alist['cy'])
                r = min(min_x + (max_x - min_x) * self.convert_offset(alist['r']),
                            min_y + (max_y - min_y) * self.convert_offset(alist['r']))
                fx = cx
                fy = cy
            #cx, cy, r, fx and fy gradient parameters are missing
            else:
                cx = min_x + (max_x - min_x) * 0.5
                cy = min_y + (max_y - min_y) * 0.5
                r  = min(cx,cy)
                fx = min_x + (max_x - min_x) * 0.5
                fy = min_y + (max_y - min_y) * 0.5

        self.cx = cx
        self.cy = cy
        self.r = r
        self.fx = fx
        self.fy = fy
        # Finally mark gradient as valid
        self._valid = True


    def to_string(self):
        # local variables
        str_buf = ''
        if len(self.stops) == 0 or self.is_valid == False:
            return str_buf

        prefix = f"radialGrad_{CB.get_current_unique_id()}"
        str_buf = self._stops_to_string(prefix,self.stops)

        str_buf += f"static radialGradient_t {CB.get_input_file_cname()}_radial_gradients_{self.grad_index}[] = {{\n"
        str_buf += f"    {{\n"
        str_buf += f"        /*grad id={self.name}*/\n"
        str_buf += f"        .num_stop_points = {len(self.stops)},\n"
        str_buf += f"        .radial_gradient = {{{self.cx}f, {self.cy}f, {self.r}f, {self.fx}f, {self.fy}f}},\n"
        str_buf += f"        .stops = {prefix}\n"
        str_buf += f"    }},\n"
        str_buf += "\n};\n\n"
        return str_buf

class PaintObject:
    def __init__(self):
        self.paint_mode = None
        self.lg = LinearGradient()
        self.rg = RadialGradient()
        self.solid = SolidColor(SVG_DEFAULT_BLACK_COLOR)
