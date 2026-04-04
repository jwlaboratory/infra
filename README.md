# infra


## Problem
We have trying to train models to improve assembly code gen, through SFT, RL, etc. In any case, having evals is important to knowing a) improvement over loss function, b) overall benchmarking. We should aim to create a opensource tool that can be used for future researchers and easily imported into any project.


## Considerations
- Should we create like a python / git module / or something (I'm not sure) to make it so we can run this benchmark easily from other projects/repos? IE, the RL can easily call this to score a generation?

- How should we standarize the benchmarking process? I think something exists to predict the # of clock cycles a given assembly code will take to run?

## Research log
April 4, 2026:
We currently use benchmarking by running assembly code locally (30 times) and averaging the time it takes to run the actual compiled code.
Few issues
1) Not hardware agnostic
2) Not easily reproducible
3) We use random n (30?)
4) The hardware that the code is compiled on
5) We can't easily run benchmarks from differnet repos