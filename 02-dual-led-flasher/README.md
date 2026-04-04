# Single LED Flasher

This project demonstrates how to build a simple 555 timer circuit with a single flashing LED

# Parts List

### Required Parts

| Number Required | Part Name | Notes |
| -----:| ------- | ---------- |
|  1    | 9-Volt Battery | |
|  1    | 9-Volt Battery Wiring Harness | [Amazon](https://www.amazon.com/dp/B07YBZ18VS) |
|  1    | Breadboard | [Amazon](https://www.amazon.com/dp/B07LFD4LT6) |
|  3    | ` * ` Jumper Wires | [Amazon](https://www.amazon.com/dp/B08YRGVYPV) |
|  1    | 555 Timer Chip | [Amazon](https://www.amazon.com/dp/B0CBKFMWDP) |
|  1    | 1uF Electrolytic Capacitor | [Amazon](https://www.amazon.com/dp/B0F8C4BBNT) |
|  1    | ` ** ` 100K Ohm Resistor | [Amazon](https://www.amazon.com/dp/B0B4JDHXC9) |
|  1    | ` ** ` 470K Ohm Resistor | [Amazon](https://www.amazon.com/dp/B07HDGJDVS) |
|  1    | ` ** ` 270 Ohm Resistor | [Amazon](https://www.amazon.com/dp/B07QG1VDJ9) |
|  1    | Light-Emitting Diode (LED) | [Amazon](https://www.amazon.com/dp/B0G4LV2DZ6) |

` * ` Three short jumper wires, 2-inches or less

` ** ` Standard non-polarized resistor. That is, it dosen't matter which direction current flows through the resistors, so it won't matter how you connect them

The capacitor and LED *are* polarized, so you'll need to identify their positive (+)
and negative (-) terminal wires, and ensure that current flows through them in the
correct direction. The build steps below will explain how to identify and properly
connect them in the circuit.

### Optional Parts

| Part Name | Notes |
| --------- | ----- |
| Multi-function Wire Stripping/Cutting Pliers | For trimming and stripping wires as needed ([Amazon](https://www.amazon.com/dp/B08Y6GDS61)) |

## Step 1: Breadboard Orientation

Place the breadboard on a flat surface, and orient it so that Row 1 is at the top from your point of view

![Orient Breadboard](../images/03/01_breadboard.png)
---

## Step 2: Add the 555 Chip

* Carefully insert your 555 timer chip with its half-moon notch pointing upward, toward the top of the breadboard

* The 4 pins on each side of the 555 should span the wide center channel that vertically 
  divides the left and right halves of your breadboard

* The horizontal row that you choose for inserting the 555 is up to you, but make sure
  to leave plenty of room below the 555 to expand downward with the remaining components

* Anywhere between row 5 and row 11 should be fine

![555 Placement](../images/03/02_add_555.png)
---

## Step 3: Connect 555's VCC [8] to Breadboard's Power Rail (+)

Use a short jumper wire to connect the 555's **VCC** pin **[8]** to the breadboard's red power rail **(+)**

![Connect VCC to Power Rail](../images/03/03_add_vcc_jumper.png)
---

## Step 4: Connect 555's GND [1] to Breadboard's Ground Rail (-)

Use a short jumper wire to connect the 555's **GND** pin **[1]** to the breadboard's blue ground rail **(-)**

![Connect GND to Ground Rail](../images/03/04_add_gnd_jumper.png)
---

## Step 5: Connect 555's TRIGGER [2] and THRESHOLD [6] pins

Use a medium jumper wire to connect the 555's **TRIGGER** pin **[2]** and **THRESHOLD** pin **[6]**

![Connect 2 to 6](../images/03/05_add_2_to_6_jumper.png)
---

## Step 6: Connect 555's RESET [4] and VCC [8] pins

Use another medium jumper wire to connect the 555's **RESET** pin **[4]** and **VCC** pin **[8]**

![Connect 4 to 8](../images/03/06_add_4_to_8_jumper.png)
---
