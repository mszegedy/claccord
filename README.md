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

- Make it maximally compatible with every keyboard layout by switching the
  backend to Xlib and using XKeyEvents to send keypresses instead.
- Make the hashing on the key combos much faster.
- Allow an arbitrary number of sets of mode keys and char keys, or at
  least sets labeled A-Z rather than just M/U/L.
- Allow switching of claccord layouts using the number keys.
- Come up with a complete suite of presets that represent the typical
  use case, and not just my personal needs. Especially come up with a
layout for IPA.
- Write an install script.
- Clean up a little.
