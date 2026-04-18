# Common 555 Applications

Due to the flexibility of the 555's different operating modes, there are literally thousands of unique 555-based
circuits in use across industrial, commercial and hobbyist applications. Here are a few common use cases:

### Square Wave Generator/Oscillator ("Astable" mode)

This mode of 555 operation is ideal for LED flashers,
buzzer drivers, clock signals, strobe lights, and any application requiring an oscillating High/Low (On/Off)
pattern that operates **continuously** until the circuit is powered off. This is the primary use case we'll be
exploring in our projects here.
  
### "One-Shot" Timer ("Monostable" mode)

This mode of operation provides a single High/Low (On/Off) cycle when triggered. This mode is ideal for delayed-start
timers, touch switches, and "anti-debounce" button switches (i.e., a mechanical switch combined with a circuit that is
designed to eliminate "bounce". Bounce in this context is the rapid, unintended opening and closing of electrical
contacts that can occur during a single button press)

### Flip-Flop Switch ("Bistable" mode)

In this mode, the 555 operates as a simple "latch", acting as an On/Off (toggle) switch to hold a state until
triggered otherwise. This mode is ideal for "power" buttons on electronically-controlled devices, and numerous
other applications requiring a manually-triggered on/off state.

