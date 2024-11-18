# STM32F072_dual_VCP
Add Virtual COM Ports to STM32F072RB DISCO dev board

Ported from:
https://github.com/GaryLee/stm32f103_dual_vcp/tree/master

but that code is a few years old...

# Dev Environment:
- STM32CubeMX 6.12.1
- STM32CubeIDE 1.16.1
- STMCube FW_F0 V1.11.5

# Hardware:
- STM32F072RBT6 uP, 32F072BDISCOVERY dev board
- 128 Kbytes Flash, 16 Kbytes SRAM
- USB full-speed

# Instructions:
Generate a basic dev environment using the IOC file (or your own) with STM32CubeMX, then copy the listed modified USB files, sample main.c .
 Anytime the IOC is changed and code regenerated you'll have to re-copy files.
- For STM32CubeMX, In the "Code Generator" section verify "Copy only the necessary library files". Otherwise the IDE will reference the repository, not the copied files.

# Modified Files:
- Class\CDC\Src\usbd_cdc.c
- Class\CDC\Inc\usbd_cdc.h
- USB_DEVICE\App\usbd_cdc_if.c
- USB_DEVICE\App\usbd_cdc_if.h
- USB_DEVICE\App\usbd_desc.c
- USB_DEVICE\App\usb_device.c
- USB_DEVICE\Target\usbd_conf.c
- USB_DEVICE\Target\usbd_conf.h
- Core\Src\main.c

# Testing
- verify 2 COM ports appear (Windows 10).
- Optionally use USBDeview (from www.nirsoft.net) to show USB devices. Observe STM32 Virtual ComPort	USB Composite Device.
- serial_loop_STM32F072.py passes and verifies serial data between the Virtual Com Ports (works on Windows 10).
