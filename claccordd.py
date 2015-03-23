#!/usr/bin/python

#### claccordd.py
#### by mszegedy
#### this is protected under the GNU GPL; the GPL text will be added in future
#### versions

"""This is a docstring, I think; it's to get Vim/pylint/whatever to shut up"""

### imports
import sys
import re
import evdev

### constants
KEYDOWN = 1 # evdev events use 1 for key being pressed down and
KEYUP = 0   # 0 for key being lifted back up
COMPOSE_KEY = 'LEFTMETA'
SHIFT_KEY = 'LEFTSHIFT'
CTRL_KEY = 'LEFTCTRL'
ALT_KEY = 'LEFTALT'
MODE_KEYS_MAP = {
    0:'A',
    1:'S',
    2:'D',
    3:'F',
    4:'G'}
CHAR_KEYS_MAP = {
    0:'H',
    1:'J',
    2:'K',
    3:'L',
    4:'SEMICOLON',
    5:'APOSTROPHE'}
ACCENTED_VOWEL_MAP = {
    'á':'A',
    'Á':'A',
    'é':'E',
    'É':'E',
    'í':'I',
    'Í':'I',
    'ó':'O',
    'Ó':'O',
    'ú':'U',
    'Ú':'U'}
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
    '¨':[COMPOSE_KEY,SHIFT_KEY,'APOSTROPHE'],
    '˝':[COMPOSE_KEY,'EQUAL'],
    '—':[COMPOSE_KEY,'MINUS','MINUS','MINUS']}

### classes
class LayoutCombo:
    """A combo of keys that produces an output."""
    def __init__(self, mode, char_keys, output):
        ## build input keys
        self.mode_keys = []
        self.char_keys = []
        # build mode keys
        for place, sign in enumerate(mode):
            if sign == '*':
                keycode = evdev.ecodes.ecodes['KEY_'+MODE_KEYS_MAP[place]]
                self.mode_keys.append(keycode)
        # build char keys
        for place, sign in enumerate(char_keys):
            if sign == '*':
                keycode = evdev.ecodes.ecodes['KEY_'+CHAR_KEYS_MAP[place]]
                self.char_keys.append(keycode)
        ## build output keys
        self.output_keys = []
        lowercase_letter_matcher = re.compile(r'[a-z]')
        uppercase_letter_matcher = re.compile(r'[A-Z]')
        lc_accented_vowel_matcher = re.compile(r'[áéóíú]')
        uc_accented_vowel_matcher = re.compile(r'[ÁÉÓÍÚ]')
        ## deal with normal uppercase and lowercase letters
        lowercase_letter_matches = lowercase_letter_matcher.match(output)
        uppercase_letter_matches = uppercase_letter_matcher.match(output)
        if uppercase_letter_matches != None or lowercase_letter_matches != None:
            if uppercase_letter_matches != None:
                self.output_keys.append(evdev.ecodes.ecodes['KEY_'+SHIFT_KEY])
            self.output_keys.append(evdev.ecodes.ecodes['KEY_'+output.upper()])
        ## deal with uppercase and lowercase accented vowels
        lc_accented_vowel_matches = lc_accented_vowel_matcher.match(output)
        uc_accented_vowel_matches = uc_accented_vowel_matcher.match(output)
        if uc_accented_vowel_matches != None or\
            lc_accented_vowel_matches != None:
            self.output_keys.append(evdev.ecodes.ecodes['KEY_'+COMPOSE_KEY])
            self.output_keys.append(evdev.ecodes.ecodes['KEY_APOSTROPHE'])
            if uc_accented_vowel_matches != None:
                self.output_keys.append(evdev.ecodes.ecodes['KEY_'+SHIFT_KEY])
            self.output_keys.append(
                evdev.ecodes.ecodes['KEY_'+ACCENTED_VOWEL_MAP[output]])
        ## deal with non-alphanumeric characters encoded by single keys
        nonalnum_key_name = None
        is_shifted = False
        try:
            nonalnum_key_name = SHIFT_NONALNUM_MAP[output]
            is_shifted = True
        except KeyError:
            pass
        try:
            nonalnum_key_name = NOSHIFT_NONALNUM_MAP[output]
        except KeyError:
            pass
        if nonalnum_key_name != None:
            if is_shifted:
                self.output_keys.append(evdev.ecodes.ecodes['KEY_'+SHIFT_KEY])
            self.output_keys.append(
                evdev.ecodes.ecodes['KEY_'+nonalnum_key_name])
        ## deal with special characters, i.e. characters that encode more than
        ## one keypress
        try:
            special_key_sequence = SPECIAL_CHARS_MAP[output]
            for key_name in special_key_sequence:
                self.output_keys.append(evdev.ecodes.ecodes['KEY_'+key_name])
        except KeyError:
            pass
        ## deal with the remainder
        if self.output_keys == []:
            print("Warning: unknown output character '"+output+"'!")
    def is_typed(self, pressed_mode_keys, pressed_char_keys):
        """Determines whether this combo has been typed, given the mode keys
        pressed and the char keys pressed."""
        return set(pressed_mode_keys) == set(self.mode_keys) and\
            set(pressed_char_keys) == set(self.char_keys)
    def type_out(self, ui):
        """Types the character or character sequence represented by this
        combination."""
        SHIFT_KEYCODE = evdev.ecodes.ecodes['KEY_'+SHIFT_KEY]
        CTRL_KEYCODE = evdev.ecodes.ecodes['KEY_'+CTRL_KEY]
        ALT_KEYCODE = evdev.ecodes.ecodes['KEY_'+ALT_KEY]
        held_mod_keys = []
        for keycode in self.output_keys:
            if keycode in (SHIFT_KEYCODE, CTRL_KEYCODE, ALT_KEYCODE):
                ui.write(evdev.ecodes.EV_KEY, keycode, KEYDOWN)
                held_mod_keys.append(keycode)
            else:
                ui.write(evdev.ecodes.EV_KEY, keycode, KEYDOWN)
                ui.write(evdev.ecodes.EV_KEY, keycode, KEYUP)
        for keycode in held_mod_keys[::-1]: # reverse order; doesn't matter
            ui.write(evdev.ecodes.EV_KEY, keycode, KEYUP)
        ui.syn()

### program
## process the layout file
try:
    layout_file = open('layout.txt', 'r')
except FileNotFoundError:
    print("Missing layout file!")
    sys.exit()
layout_combos = []
file_mode = None
line_count = 0
for line in layout_file:
    line_count += 1
    file_mode_line_matcher = re.compile(r'([-*]{4,}):.*')
    char_line_matcher = re.compile(r' ([-* ]{6}) (.).*')
    file_mode_line_matches = file_mode_line_matcher.match(line)
    if file_mode_line_matches != None: # it's a file_mode line
        file_mode = file_mode_line_matches.group(1)
    else:
        char_line_matches = char_line_matcher.match(line)
        if char_line_matches != None: # it's a char line
            layout_combos.append(
                LayoutCombo(
                    file_mode,
                    char_line_matches.group(1),
                    char_line_matches.group(2)))
        else:
            print("Invalid layout file! Error on line "+str(line_count))
## start keyboarding
ui = evdev.UInput()
kb = evdev.InputDevice('/dev/input/event0')
kb.grab()
mode_keys_active = set([])
char_keys_active = set([])
for event in kb.read_loop():
    if event.type == evdev.ecodes.EV_KEY:
        key_event = evdev.categorize(event)
        if key_event.keystate == KEYDOWN:
            if key_event.scancode == evdev.ecodes.ecodes['KEY_ESC']:
                ui.close()
                kb.ungrab()
                sys.exit()
            if key_event.scancode in [evdev.ecodes.ecodes['KEY_'+c] for c in\
                MODE_KEYS_MAP.values()]:
                mode_keys_active.add(key_event.scancode)
            elif key_event.scancode in [evdev.ecodes.ecodes['KEY_'+c] for c in\
                CHAR_KEYS_MAP.values()]:
                char_keys_active.add(key_event.scancode)
            else:
                ui.write_event(event)
                ui.syn()
        elif key_event.keystate == KEYUP:
            ## if it's a change in the mode keys:
            if key_event.scancode in [evdev.ecodes.ecodes['KEY_'+c] for c in\
                MODE_KEYS_MAP.values()]:
                mode_keys_active.remove(key_event.scancode)
            else:
                ## figure out whether any char keys are being held down
                active_keys = kb.active_keys()
                char_keys_are_active = False
                for key_name in CHAR_KEYS_MAP.values():
                    if evdev.ecodes.ecodes['KEY_'+key_name] in active_keys:
                        char_keys_are_active = True
                        break
                ## if no char keys are pressed, type the character
                if not char_keys_are_active:
                    ## figure out what combo this is
                    pressed_layout_combo = None
                    for layout_combo in layout_combos:
                        if layout_combo.is_typed(
                            mode_keys_active,
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
