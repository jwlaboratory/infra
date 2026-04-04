# infra


## Problem
We have trying to train models to improve assembly code gen, through SFT, RL, etc. In any case, having evals is important to knowing a) improvement over loss function, b) overall benchmarking. We should aim to create a opensource tool that can be used for future researchers and easily imported into any project.


## Considerations
- Should we create like a python / git module / or something (I'm not sure) to make it so we can run this benchmark easily from other projects/repos? IE, the RL can easily call this to score a generation?

- How should we standarize the benchmarking process? I think something exists to predict the # of clock cycles a given assembly code will take to run?

## Research log
April 4, 2026 - Shrey:
We currently use benchmarking by running assembly code locally (30 times) and averaging the time it takes to run the actual compiled code.
Few issues
1) Not hardware agnostic
2) Not easily reproducible
3) We use random n (30?)
4) The hardware that the code is compiled on
5) We can't easily run benchmarks from differnet repos

Our scorer should check:
1. Does the assembly code compile?
2. Does it match the original code?
    a) Either it passes all original test cases (heuristic)
    b) Or it is formally verified to be identical program?
3. Static performance metrics (number of clock cycles, memory usage, etc.)? 
    a) Issue with this is that it doesn't seem to account for dynamic behavior (e.g. cache misses, branch predictions, etc.)
4. Google benchmark? Isolated containers? Linux `perf` containers?

We should be an open source framework people can tweak the scoring logic to their needs I think.
Imagine you can pass in:
 - scoring framework
 - assembly generated code
 - C code
 - target hardware
 - test cases

 Output
  - score
  - dynamic performance metrics
  - pass test cases / verification of code 
  - memory, static performance metrics

  Let's start with naive implementation in `naive` so that we can unblock other teams requiring benchmarking.