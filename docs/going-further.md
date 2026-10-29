# Going further

`archsim` is deliberately small. These are the tools and courses to turn to
when its simplifications start to matter.

## Modelling tools

* **Timeloop** and **Accelergy** (MIT and NVIDIA) map a DNN layer onto an
  accelerator described as a hierarchy of buffers and compute units, search
  the mappings, and estimate energy and area from component models. Timeloop
  does properly what Lab 1 and Lab 2 do by hand.
* **Gemmini** (UC Berkeley) is an open-source generator of systolic-array
  accelerators integrated with RISC-V cores, with a full software stack. It is
  the place to see output- and weight-stationary dataflows in real RTL.

## Reconfigurable arrays

The toy CGRA of Lab 3 hints at a middle ground between fixed-function units
and programmable cores. NX-CGRA (R. Prasad, DATE 2026) is a recent example,
a programmable hardware accelerator for the core Transformer algorithms on
edge devices.

## Courses

* MIT 6.5940, *TinyML and Efficient Deep Learning Computing* (Song Han).
* MIT 6.5930/6.5931, *Hardware Architecture for Deep Learning* (Vivienne Sze and Joel Emer).
* Stanford CS217, *Hardware Accelerators for Machine Learning*.
* CMU 10-414/714, *Deep Learning Systems* (Tianqi Chen and Zico Kolter).

## Reading

* V. Sze, Y.-H. Chen, T.-J. Yang and J. S. Emer, *Efficient Processing of Deep
  Neural Networks*, the tutorial paper (2017) and the book that followed.
* The papers on the [References](references.md) page, in the order the labs use them.
