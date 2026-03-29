# Dual LED Flasher with Rotary Potentiometer

This project demonstrates how to build a 555 timer circuit with dual flashing LEDs and utilizing a rotary potentiomenter for modifying LED flash frequency

## Parts List

| Number Required | Part Name | Notes |
| ----- | --------- | ---------- |
|  1    | 9-Volt Battery + Wiring Harness | [Amazon](https://www.amazon.com/dp/B07YBZ18VS) |
|  1    | Breadboard | [Amazon](https://www.amazon.com/dp/B07LFD4LT6) |
|  7    | Jumper Wires | [Amazon](https://www.amazon.com/dp/B08YRGVYPV) |
|  1    | 555 Timer Chip | [Amazon](https://www.amazon.com/dp/B0CBKFMWDP) |
|  1    | 100 uF Electrolytic Capacitor | [Amazon](https://www.amazon.com/dp/B0FS1KSBK5) |
|  1    | 1K Ohm Resistor | [Amazon](https://www.amazon.com/dp/B0FP1YFMVM) |
|  2    | 270 Ohm Resistor | [Amazon](https://www.amazon.com/dp/B07QG1VDJ9) |
|  2    | 1N4007 Rectifier Diode | [Amazon](https://www.amazon.com/dp/B0FC2CQF24) |
|  2    | LED | [Amazon](https://www.amazon.com/dp/B0G4LV2DZ6) |
|  1    | 10K Rotary Potentiometer | [Amazon](https://www.amazon.com/dp/B071ZVNFJ8) |

## Circuit Build Steps

### Step 1:

   Orient your breadboard with row 1 at the top.

   From your point of view, make sure that the breadboards's outer power (+) and ground (-) rails
   appear vertically, and from left to right in this order:

   | Red (+) | Blue (-) .... || .... Red (+) | Blue (-) |

   ![Orient Breadboard](../images/03/01_breadboard.png)

---
### Step 2:

   Carefully insert your 555 timer chip into the breadboard. The row that you choose is up
   to you. What is important is that the 555's ground (pin 1 or "GND") is on the left side of the
   breadboard and "VCC" (pin 8) on the right side of the breadboard. If the 555's "half moon"
   notch is oriented upward, you're good to go

   ![555 Placement](../images/03/02_add_555.png)

---
### Step 3:

   Use a small jumper wire to connect VCC (pin 8) to the breadboard's red power (+) rail

   ![Connect VCC to Power Rail](../images/03/03_add_vcc_jumper.png)

---
### Step 4:

   Use a small jumper wire to connect the 555's GND (pin 1) to the breadboard's blue ground (-) rail

   ![Connect GND to Ground Rail](../images/03/04_add_gnd_jumper.png)

---
### Step 5:

   Use a slightly longer jumper wire to connect the 555's TRIGGER (pin 2) to THRESHOLD (pin 6)

   ![Connect 2 to 6](../images/03/05_add_2_to_6_jumper.png)

---
### Step 6:

   Use another similarly-sized jumper to connect the 555's RESET (pin 4) to VCC (pin 8)

   ![Connect 4 to 8](../images/03/06_add_4_to_8_jumper.png)

---
### Step 7:

   Connect the 100 uF capacitor to the 555's TRIGGER (pin 2). The capacitor's positive pole (long leg, or "anode")
   should connect to the 555's pin 2, and the capacitor's negative pole (short leg, or "cathode") should be connected
   to the breadboard's blue ground (-) rail

   ![Add 100uF capacitor](../images/03/07_add_100uf_capacitor.png)





