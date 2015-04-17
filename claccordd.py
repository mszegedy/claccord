#!/usr/bin/python

#### claccordd.py
#### by mszegedy
#### this is protected under the GNU GPL; the GPL text will be added in future
#### versions

"""This is a docstring, I think; it's to get Vim/pylint/whatever to shut up"""

### imports
import sys
import copy
import re
import evdev

### constants
KEYDOWN = 1 # evdev events use 1 for key being pressed down and
KEYUP = 0   # 0 for key being lifted back up
COMPOSE_KEY = 'LEFTMETA'
SHIFT_KEY = 'LEFTSHIFT'
CTRL_KEY = 'LEFTCTRL'
ALT_KEY = 'LEFTALT'
M_MODE_KEYS_MAP = {
    0:'A',
    1:'S',
    2:'D',
    3:'F',
    4:'G'}
M_CHAR_KEYS_MAP = {
    0:'H',
    1:'J',
    2:'K',
    3:'L',
    4:'SEMICOLON',
    5:'APOSTROPHE'}
U_MODE_KEYS_MAP = {
    0:'Q',
    1:'W',
    2:'E',
    3:'R',
    4:'T'}
U_CHAR_KEYS_MAP = {
    0:'Y',
    1:'U',
    2:'I',
    3:'O',
    4:'P',
    5:'LEFTBRACE'}
L_MODE_KEYS_MAP = {
    0:'Z',
    1:'X',
    2:'C',
    3:'V',
    4:'B'}
L_CHAR_KEYS_MAP = {
    0:'N',
    1:'M',
    2:'COMMA',
    3:'DOT',
    4:'SLASH'}
NOSHIFT_NONALNUM_MAP = {
    '.':'DOT',
    ',':'COMMA',
    '\'':'APOSTROPHE',
    ';':'SEMICOLON',
    '-':'MINUS',
    '[':'LEFTBRACE',
    ']':'RIGHTBRACE',
    '/':'SLASH',
    '=':'EQUAL',
    '\\':'BACKSLASH'}
SHIFT_NONALNUM_MAP = {
    ':':'SEMICOLON',
    '(':'9',
    ')':'0',
    '{':'LEFTBRACE',
    '}':'RIGHTBRACE',
    '"':'APOSTROPHE',
    '?':'SLASH',
    '!':'1',
    '*':'8',
    '+':'EQUAL',
    '<':'COMMA',
    '>':'DOT',
    '^':'6',
    '&':'7',
    '|':'BACKSLASH',
    '#':'3'}
SPECIAL_CHARS_MAP = {
    '+PAGE_UP':['PAGEUP'],
    '+PAGE_DOWN':['PAGEDOWN'],
    '+ESC':['ESC'],
    '+VIM_BLOCKWISE_VISUAL':[CTRL_KEY, 'V']}

### classes
class Keypress:
    """A single keypress, to be used in the output keys in LayoutCombo."""
    def __init__(self, key_name):
        self.key_name = key_name
        self.heldp = False
        self.keyupp = False
        if key_name in (SHIFT_KEY, CTRL_KEY, ALT_KEY, 'U_HELD'):
            self.heldp = True
        if key_name[-5:] == '_HELD':
            key_name = key_name[:-5]
        if key_name[-6:] == '_KEYUP':
            self.keyupp = True
            key_name = key_name[:-6]
        self.keycode = evdev.ecodes.ecodes['KEY_'+key_name]

class LayoutCombo:
    """A combo of keys that produces an output."""
    def __init__(self, mode_code, char_code, output_code,
            mode_position='M', char_position='M'):
        self.mode_code = mode_code
        self.char_code = char_code
        self.output_code = output_code
        self.mode_position = mode_position
        self.char_position = char_position
    def compile(self):
        """Sets self.mode_keys and self.char_keys based on the saved mode_code
        and char_code."""
        mode_code = self.mode_code
        char_code = self.char_code
        output_code = self.output_code
        # build mode keys
        self.set_mode(mode_code, mode_position)
        # build char keys
        self.set_char(char_code, char_position)
        ## build output keys
        self.output_keys = []
        category = self.get_category()
        ## deal with normal uppercase and lowercase letters
        if category in ('ALNUM_LOWER', 'ALNUM_UPPER'):
            if category[-6:] == '_UPPER':
                self.output_keys.append(Keypress(SHIFT_KEY))
            self.output_keys.append(Keypress(output_code.upper()))
        ## deal with non-alphanumeric characters encoded by single keys
        elif category in ('NONALNUM','NONALNUM_SHIFTED'):
            nonalnum_key_name = None
            if category[-8:] == '_SHIFTED':
                self.output_keys.append(Keypress(SHIFT_KEY))
                nonalnum_key_name = SHIFT_NONALNUM_MAP[output_code]
            else:
                nonalnum_key_name = NOSHIFT_NONALNUM_MAP[output_code]
            self.output_keys.append(Keypress(nonalnum_key_name))
        ## deal with special characters, i.e. codes; codes must begin with a
        ## plus sign, and have the rest consist of uppercase letters and
        ## underscores
        elif category == 'SPECIAL':
            try:
                special_key_sequence = SPECIAL_CHARS_MAP[output_code]
                typablep = True
                for key_name in special_key_sequence:
                    self.output_keys.append(Keypress(key_name))
            except KeyError:
                print("Warning: probably an invalid special sequence code on "
                      "line" + str(line_count) + "!")
        ## deal with everything else; it will just type out the given Unicode
        ## characters
        elif category == 'UNICODE_SEQ':
            for char in output_code:
                # convert character to sequence, convert sequence to hex, lop
                # off the '0x' in front
                unicode_sequence = hex(ord(char))[2:]
                self.output_keys.extend((Keypress(key_name) for\
                    key_name in\
                    (CTRL_KEY, SHIFT_KEY, 'U_HELD') +\
                    tuple(unicode_sequence.upper()) +\
                    ('U_KEYUP', SHIFT_KEY+'_KEYUP', CTRL_KEY+'_KEYUP')))
    def get_category(self):
        output_code = self.output_code
        lowercase_letter_matcher = re.compile(r'^[a-z]$')
        lowercase_letter_matches = lowercase_letter_matcher.match(output_code)
        if lowercase_letter_matches != None:
            return 'ALNUM_LOWER'
        uppercase_letter_matcher = re.compile(r'^[A-Z]$')
        uppercase_letter_matches = uppercase_letter_matcher.match(output_code)
        if uppercase_letter_matches != None:
            return 'ALNUM_UPPER'
        nonalnum_key_name = None
        is_shifted = False
        try:
            nonalnum_key_name = SHIFT_NONALNUM_MAP[output_code]
            return 'NONALNUM_SHIFTED'
        except KeyError:
            pass
        try:
            nonalnum_key_name = NOSHIFT_NONALNUM_MAP[output_code]
            return 'NONALNUM'
        except KeyError:
            pass
        special_code_matcher = re.compile(r'\+[A-Z_]+')
        special_code_matches = special_code_matcher.match(output_code)
        if special_code_matches != None:
            return 'SPECIAL'
        return 'UNICODE_SEQ'
    def get_layout_combos_key(self):
        return self.mode_code+'@'+self.char_code+'@'+\
            self.mode_position+self.char_position
    def set_mode(self, mode_code, mode_position=None):
        self.mode_code = mode_code
        self.mode_keys = []
        if mode_position != None:
            self.mode_position = mode_position
        else:
            mode_position = self.mode_position
        mode_keys_map = {}
        if mode_position == 'M':
            mode_keys_map = M_MODE_KEYS_MAP
        elif mode_position == 'U':
            mode_keys_map = U_MODE_KEYS_MAP
        elif mode_position == 'L':
            mode_keys_map = L_MODE_KEYS_MAP
        for place, sign in enumerate(mode_code):
            if sign == '*':
                self.mode_keys.append(Keypress(mode_keys_map[place]))
    def set_char(self, char_code, char_position=None):
        self.char_code = char_code
        self.char_keys = []
        if char_position != None:
            self.char_position = char_position
        else:
            char_position = self.char_position
        char_keys_map = {}
        if char_position == 'M':
            char_keys_map = M_CHAR_KEYS_MAP
        elif char_position == 'U':
            char_keys_map = U_CHAR_KEYS_MAP
        elif char_position == 'L':
            char_keys_map = L_CHAR_KEYS_MAP
        for place, sign in enumerate(char_code):
            if sign == '*':
                self.char_keys.append(Keypress(char_keys_map[place]))
    def typedp(self, pressed_mode_keys, pressed_char_keys):
        """Determines whether this combo has been typed, given the mode keys
        pressed and the char keys pressed."""
        mode_keys_keycodes = set((keypress.keycode\
            for keypress in self.mode_keys))
        char_keys_keycodes = set((keypress.keycode\
            for keypress in self.char_keys))
        return set(pressed_mode_keys) == mode_keys_keycodes and\
            set(pressed_char_keys) == char_keys_keycodes
    def type_out(self, ui):
        """Types the character or character sequence represented by this
        combination."""
        held_mod_keys = []
        for keypress in self.output_keys:
            if keypress.heldp:
                ui.write(evdev.ecodes.EV_KEY, keypress.keycode, KEYDOWN)
                print(keypress.key_name+" DOWN")
                held_mod_keys.append(keypress)
            elif keypress.keyupp:
                ui.write(evdev.ecodes.EV_KEY, keypress.keycode, KEYUP)
            else:
                ui.write(evdev.ecodes.EV_KEY, keypress.keycode, KEYDOWN)
                print(keypress.key_name+" DOWN")
                ui.write(evdev.ecodes.EV_KEY, keypress.keycode, KEYUP)
                print(keypress.key_name+" UP")
        for keypress in held_mod_keys[::-1]: # reverse order; doesn't matter
            ui.write(evdev.ecodes.EV_KEY, keypress.keycode, KEYUP)
            print(keypress.key_name+" UP")
        ui.syn()

### program
## process the layout file
try:
    layout_file = open('layout.txt', 'r')
except FileNotFoundError:
    print("Missing layout file!")
    sys.exit()
# layout_combos: dictionary for storing the possible combos to press; keys are
# the mode code, char code, mode position, and char position concatenated
# together
layout_combos = {} 
file_mode = None
line_count = 0
for line in layout_file:
    line_count += 1
    # absolutely disgusting:
    mode_line_matcher =\
        re.compile(
            r'([MUL])?([-*]{4,})'
            r'((:)|=\s*((S\+|C\+|M\+)*)([MUL])?([-*]{4,}))\s*(#.*)?')
    # match groups:
    # 0: the whole line, if it's a valid mode line
    # 1: the position modifier of the mode keys, if any
    # 2: the keys of the mode this is defining
    # 3: the rest of the line that isn't a comment
    # 4: the colon, if it's an original mode and not a copied one
    # 5: the modifier keys, if it's a copied mode
    # 6: the last modifier key, if it's a copied mode
    # 7: the position of the mode it's copying from, if any
    # 8: the keys of mode it's copying from, if any
    # 9: the comment, if any
    char_line_matcher = re.compile(r'([ MUL])([-* ]{6}) (.+);\s*(#.*)?')
    # match groups:
    # 0: the whole line, if it's a valid char line
    # 1: the position modifier of the char keys, if any
    # 2: the keys of the char that this is defining
    # 3: the char that this is defining
    # 4: the comment, if any
    mode_line_matches = mode_line_matcher.match(line)
    if mode_line_matches != None: # it's a mode line
        mode = mode_line_matches.group(2)
        mode_position = 'M'
        if mode_line_matches.group(1) != None:
            mode_position = mode_line_matches.group(1)
        if mode_line_matches.group(4) != None:
            pass
        else: # if this mode is a copy of another
            modifier_keys = []
            if mode_line_matches.group(5) != None:
                for modifier in mode_line_matches.group(5).split('+')[:-1]:
                    if modifier == 'S':
                        modifier_keys.append(Keypress(SHIFT_KEY))
                    elif modifier == 'C':
                        modifier_keys.append(Keypress(CTRL_KEY))
                    elif modifier == 'M':
                        modifier_keys.append(Keypress(ALT_KEY))
            for layout_combo in\
                [layout_combos[layout_combo_key] for layout_combo_key in\
                 layout_combos.keys() if\
                 layout_combos[layout_combo_key].mode_code ==\
                mode_line_matches.group(8) and\
                layout_combo.mode_position ==\
                ('M' if mode_line_matches.group(7) == None else\
                 mode_line_matches.group(7))]:
                layout_combo_copy = copy.deepcopy(layout_combo)
                layout_combo_copy.set_mode(mode, mode_position)
                layout_combo_copy.output_keys[0:0] = modifier_keys
                layout_combos[layout_combo_copy.get_layout_combos_key()] =\
                    layout_combo_copy
        continue
    char_line_matches = char_line_matcher.match(line)
    if char_line_matches != None: # it's a char line
        char_position = 'M'
        if char_line_matches.group(1) != ' ':
            char_position = char_line_matches.group(1)
        layout_combo = LayoutCombo(mode,
                                   char_line_matches.group(2),
                                   char_line_matches.group(3),
                                   mode_position,
                                   char_position)
        layout_combo.compile()
        layout_combos[layout_combo.get_layout_combos_key()] = layout_combo
        continue
    print("Invalid layout file! Error on line "+str(line_count))
## start keyboarding
for key in layout_combos.keys():
    print(key+" : "+layout_combos[key].output_code+" : "+\
            str([keypress.key_name for keypress in layout_combos[key].output_keys]))
ui = evdev.UInput()
kb = evdev.InputDevice('/dev/input/event0')
kb.grab()
mode_keys_active = set([])
char_keys_active = set([])
ALL_MODE_KEYS = set(tuple(M_MODE_KEYS_MAP.values()) +
                    tuple(U_MODE_KEYS_MAP.values()) +
                    tuple(L_MODE_KEYS_MAP.values()))
ALL_CHAR_KEYS = set(tuple(M_CHAR_KEYS_MAP.values()) +
                    tuple(U_CHAR_KEYS_MAP.values()) +
                    tuple(L_CHAR_KEYS_MAP.values()))
for event in kb.read_loop():
    if event.type == evdev.ecodes.EV_KEY:
        key_event = evdev.categorize(event)
        if key_event.keystate == KEYDOWN:
            if key_event.scancode == evdev.ecodes.ecodes['KEY_ESC']:
                ui.close()
                kb.ungrab()
                sys.exit()
            if key_event.scancode in [evdev.ecodes.ecodes['KEY_'+c] for c in\
                ALL_MODE_KEYS]:
                mode_keys_active.add(key_event.scancode)
            elif key_event.scancode in [evdev.ecodes.ecodes['KEY_'+c] for c in\
                ALL_CHAR_KEYS]:
                char_keys_active.add(key_event.scancode)
            else:
                ui.write_event(event)
                ui.syn()
        elif key_event.keystate == KEYUP:
            ## if it's a change in the mode keys:
            if key_event.scancode in [evdev.ecodes.ecodes['KEY_'+c] for c in\
                ALL_MODE_KEYS]:
                mode_keys_active.remove(key_event.scancode)
            else:
                ## figure out whether any char keys are being held down
                active_keys = kb.active_keys()
                char_keys_are_active = False
                for key_name in ALL_CHAR_KEYS:
                    if evdev.ecodes.ecodes['KEY_'+key_name] in active_keys:
                        char_keys_are_active = True
                        break
                ## if no char keys are pressed, type the character
                if not char_keys_are_active:
                    ## figure out what combo this is
                    pressed_layout_combo = None
                    for layout_combo in layout_combos.values():
                        if layout_combo.typedp(mode_keys_active,
                                               char_keys_active):
                            pressed_layout_combo = layout_combo
                            break
                    if pressed_layout_combo != None:
                        ## type the combo
                        pressed_layout_combo.type_out(ui)
                    else:
                        ui.write_event(event)
                        ui.syn()
                    # zero out the active char keys
                    char_keys_active = set([])
        else:
            ui.write_event(event)
            ui.syn()
