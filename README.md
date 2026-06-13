# AudioBox

## Introduction
I have always wanted to be able to play sound effects from an actual device where I can just smack the button and the effect will play without having to use my phone.

Then, I thought, what if I created a device that is just a button

From there, I thought how can I make this project unique.

This project is powered by a Seeed Xiao RP2040 because it is affordable and has a large flash size. It is tiny too.

Next, I added 3W 8Ω speakers that can go up to 110DB!! That is to ensure that the sound effect can be heard even in a loudroom

Instead of using traditional buttons, I decided to go with limit switches so that the user can experience the satisfying click sound when the button is pressed

To reduce static noise, I added a decoupling and a bypass capacitor to the circuit. This will help to ensure that there is no static noise

## Images
![image 1](images/Screenshot%202026-06-13%20at%205.24.10%E2%80%AFPM.png)
![image 2](images/Screenshot%202026-06-13%20at%205.24.14%E2%80%AFPM.png)
![image 3](images/Screenshot%202026-06-13%20at%205.26.17%E2%80%AFPM.png)
![image 4](images/Screenshot%202026-06-13%20at%205.27.15%E2%80%AFPM.png)

## BOM
# Bill of Materials (BOM)

| Item | Qty | Unit Cost (USD) | Total Cost (USD) |
|------|-----|-----------------|------------------|
| PCB + PCBA | 1 | 37.02 | 37.02 |
| Speaker | 2 | 2.30 | 4.60 |
| SS-5GL | 2 | 1.60 | 3.20 |
| Seeed XIAO RP2040 | 1 | 3.71 | 3.71 |
| **Total** |  |  | **48.53** |

## Future Plans

I plan on creating a website once the hardware is done to talk to the RP2040, to download and install new audio

This makes it a well-polished product, rather than having to open up the code just to change the audio

If not for this feature, I would have just used a normal pcb audio player and no need for the rp2040