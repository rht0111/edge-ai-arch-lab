# References

Every source cited in the labs, on this site or in the code.

## Energy and area figures

- M. Horowitz, "Computing's energy problem (and what we can do about it)",
  *IEEE International Solid-State Circuits Conference (ISSCC)*, 2014, pp. 10-14.
  Source of the 45 nm arithmetic energies and areas, the 8 KB / 32 KB / 1 MB SRAM
  read energies and the DRAM range used in `archsim/energy.py`.

Values marked *interpolated* or *assumed* in `archsim/energy.py` (4- and
16-bit multipliers, flip-flop area, SRAM area per KiB, LUT read, cost of
software exp/tanh/div/rsqrt) and in `archsim/design.py` (host core, leakage,
unit lanes) are the course's own estimates, not taken from a publication.
They are chosen to be plausible and to keep the ratios right. Treat them,
like every number in `archsim`, as illustrative.

## Performance models and dataflows

- S. Williams, A. Waterman and D. Patterson, "Roofline: an insightful visual
  performance model for multicore architectures", *Communications of the ACM*
  52(4), 2009.
- H. T. Kung, "Why systolic architectures?", *IEEE Computer* 15(1), 1982.
- Y.-H. Chen, J. Emer and V. Sze, "Eyeriss: a spatial architecture for
  energy-efficient dataflow for convolutional neural networks", *ISCA* 2016.
- V. Sze, Y.-H. Chen, T.-J. Yang and J. S. Emer, "Efficient processing of
  deep neural networks: a tutorial and survey", *Proceedings of the IEEE*
  105(12), 2017.
- N. P. Jouppi et al., "In-datacenter performance analysis of a tensor
  processing unit", *ISCA* 2017.

## Transformers and their non-linear functions

- A. Vaswani et al., "Attention is all you need", *NeurIPS* 2017.
- A. Dosovitskiy et al., "An image is worth 16x16 words: Transformers for
  image recognition at scale", *ICLR* 2021.
- H. Touvron et al., "Training data-efficient image transformers and
  distillation through attention", *ICML* 2021. Source of the ViT-Tiny (DeiT-Ti)
  configuration, with 12 blocks, embedding 192, 3 heads and about 5.7 M parameters.
- D. Hendrycks and K. Gimpel, "Gaussian error linear units (GELUs)",
  arXiv:1606.08415, 2016. Tanh and sigmoid approximations of GELU.
- S. Kim, A. Gholami, Z. Yao, M. W. Mahoney and K. Keutzer, "I-BERT:
  integer-only BERT quantization", *ICML* 2021. Polynomial exp and erf used in
  `archsim/nonlinear.py` (coefficients 0.3585, 1.353, 0.344 and
  a = -0.2888, b = -1.769).
- T. Dao, D. Y. Fu, S. Ermon, A. Rudra and C. Ré, "FlashAttention: fast and
  memory-efficient exact attention with IO-awareness", *NeurIPS* 2022.

## Tools and examples (Going further)

- A. Parashar et al., "Timeloop: a systematic approach to DNN accelerator
  evaluation", *ISPASS* 2019.
- Y. N. Wu, J. S. Emer and V. Sze, "Accelergy: an architecture-level energy
  estimation methodology for accelerator designs", *ICCAD* 2019.
- H. Genc et al., "Gemmini: enabling systematic deep-learning architecture
  evaluation via full-stack integration", *DAC* 2021.
- R. Prasad, "NX-CGRA: A Programmable Hardware Accelerator for Core
  Transformer Algorithms on Edge Devices", *2026 Design, Automation & Test in
  Europe Conference (DATE)*, Verona, Italy, 2026, pp. 1-7, DOI
  [10.23919/DATE69613.2026.11539188](https://doi.org/10.23919/DATE69613.2026.11539188).

## Courses (Going further)

- MIT 6.5940, TinyML and Efficient Deep Learning Computing.
- MIT 6.5930/6.5931, Hardware Architecture for Deep Learning.
- Stanford CS217, Hardware Accelerators for Machine Learning.
- CMU 10-414/714, Deep Learning Systems.
