#claccord
Allows advanced, highly-configurable keychording, based on the paradigm
of switching through different "modes" with one hand, and executing
chording combos with the other. It's the best thing I've coded since
sliced bread, and I currently use it to type. It's a bit of a mess at
the moment, but I very much plan to see it through to a
widely-compatible end. Requires the library `evdev` for Python, and must
be run as root. Non-alphanumeric characters don't work in urxvt, because
it grabs the required keys to produce them for some reason.

Todo:

- Fix backend:
  - Excise `evdev`, replace with custom Xlib C++ interface wrapped with
    `ctypes`
  - Break up `claccord.py` into a server and client, and further break up
    both into libraries
  - Develop better hashing for the key combos (maybe using keymasks)
- Add features:
  - Add the option to switch between layouts using number keys
  - Make one-key mode actually work
  - Allow more sets of mode keys and char keys (currently 26 of each)
  - Make a set of standard layout files for different languages
  - Add optional exception for one or more modifier keys (so that
    claccord plays nicely with things like i3)
