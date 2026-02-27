# Challenge Design Guide

## Principles of Good Challenge Design

### 1. Grounding
Every challenge MUST reference something the agent just did.
- ❌ Bad: "What's the complexity of quicksort?" (random)
- ✅ Good: "What's the complexity of the sorting function I just wrote for the pipeline?" (grounded)

### 2. Right-Sizing (30–90 seconds per challenge)
- **Pen & Paper**: Simple arithmetic, 2–3 step derivation, single formula application
- **Explain Back**: 2–3 sentences testing one core concept
- **Predict**: One specific, concrete output (a number, a state, a shape)
- **Spot the Bug**: One clear bug, possibly one subtle secondary issue
- **Complexity**: Big-O with brief justification
- **Connect the Dots**: 2–3 sentence connection between two specific things

### 3. Unambiguity
The correct answer must be clearly defined. For numerical answers, specify precision.
For conceptual answers, have 2–3 "must-mention" key concepts in mind before presenting.

### 4. Scaffolded Difficulty

**Apprentice**: Direct application of a single concept
- "What does this function return for input [5, 3, 8]?"
- "What's 3×3 convolution output size on 28×28 with no padding?"

**Practitioner**: Combining 2 concepts or multi-step reasoning
- "This function has O(n²). How would you make it O(n log n)?"
- "Why does this ReLU activation cause dying neurons here?"

**Expert**: Deep understanding, edge case awareness, non-obvious connections
- "Why does the parameter shift rule need π/2 and not some other value?"
- "When would this barren plateau mitigation strategy fail?"

**Master**: Novel synthesis, creative problem-solving, research-level insight
- "Can you derive a tighter bound on the expressibility of this circuit?"
- "How would you modify this shadow estimation protocol for non-Clifford measurements?"

---

## Challenge Type Examples

### Type 1: Pen & Paper 📝
> 🧠 **SKILL CHECK #47** — `tensor-ops` — Difficulty: Practitioner
>
> I just wrote a function that applies a 3×3 convolution with stride=2, padding=1
> to a 28×28 single-channel input.
>
> → Grab a pen. What's the spatial dimension of the output feature map?
>
> `[answer]` `[hint]` `[skip]`

**Evaluation**: Exact match for numerical answers. Show work if wrong.

---

### Type 2: Explain Back 🗣️
> 🧠 **SKILL CHECK #48** — `quantum-circuits` — Difficulty: Expert
>
> I just used the parameter shift rule to compute the gradient of an expectation value.
>
> → In 2–3 sentences: Why is the shift exactly π/2? What property of the gate generator
> makes this work?
>
> `[answer]` `[hint]` `[skip]`

**Key concepts to check for**: eigenvalue spectrum of generator, ±1 eigenvalues of Pauli
generators → π/2 shift.

---

### Type 3: Predict the Output 🔮
> 🧠 **SKILL CHECK #49** — `quantum-circuits` — Difficulty: Expert
>
> I built a 4-qubit circuit: RBS(π/4) on qubits (0,1), then RBS(π/3) on qubits (1,2).
> Input state: |1100⟩
>
> → What is the probability of measuring qubit 2 in state |1⟩?
>
> `[answer]` `[hint]` `[skip]`

**Evaluation**: Accept ±0.01 tolerance for probabilities.

---

### Type 4: Spot the Bug 🐛
> 🧠 **SKILL CHECK #50** — `python-debugging` — Difficulty: Practitioner
>
> Here's a version of the function I just wrote, but with a bug:
> ```python
> def softmax(x):
>     exp_x = np.exp(x)
>     return exp_x / np.sum(exp_x, axis=0)
> ```
> → What's wrong, and when would it fail?
>
> `[answer]` `[hint]` `[skip]`

**Key bugs**: no max subtraction (numerical instability); `axis=0` wrong for batched inputs.

---

### Type 5: Complexity Check ⏱️
> 🧠 **SKILL CHECK #51** — `algorithms` — Difficulty: Practitioner
>
> I just wrote a function that finds all pairs in an array summing to target K.
>
> → What's the time and space complexity of my implementation?
> Bonus: Could it be done better?
>
> `[answer]` `[hint]` `[skip]`

**Evaluation**: Check Big-O notation. Bonus XP for optimization insights.

---

### Type 6: Connect the Dots 🔗
> 🧠 **SKILL CHECK #52** — `quantum-ml` — Difficulty: Expert
>
> We just implemented classical shadow estimation for this circuit.
> Earlier this week, we worked on parameter shift gradients.
>
> → What's the connection? Could classical shadows help with gradient estimation?
>
> `[answer]` `[hint]` `[skip]`

**Evaluation**: Open-ended. Award based on depth of insight.

---

## Topic-Specific Challenge Banks

### Quantum Computing
**pen-paper:** Circuit output states, RBS/Hamming weight proofs, expectation values for small
circuits, parameter shift derivations, gate decompositions.

**explain-back:** Why HHL doesn't give exponential speedup in practice; difference between
coherent and incoherent noise; barren plateau intuition; why VQE works variationaly.

**predict:** State after specific circuit sequence; measurement probability in subspace;
effect of noise channel on density matrix.

**spot-bug:** Wrong measurement basis; unnormalized state from encoding; gradient vanishes
every iteration in VQE; fidelity > 1 from indexing error.

**connect-dots:**
- Quantum Fisher information ↔ Classical Fisher information / natural gradient
- Barren plateaus ↔ Vanishing gradients / loss landscape sharpness
- Hamming weight preservation ↔ Permutation equivariance in GNNs
- Classical shadows ↔ Sketching algorithms in streaming
- QAOA ↔ Simulated annealing / continuous relaxations
- Clifford circuits ↔ Linear codes over GF(2)
- Tensor network contraction ↔ Einsum in deep learning
- VQE ↔ Expectation-maximization

---

### Machine Learning
**pen-paper:** Backprop for a single layer, cross-entropy as negative log-likelihood, Adam
update derivation, L2 reg as Gaussian prior.

**explain-back:** Why dropout works as regularization (ensemble interpretation); what attention
mechanism computes vs what CNNs do; difference between model capacity and generalization.

**predict:** Output shape through a series of layers; gradient flow in specific architecture;
what BatchNorm does differently at train vs eval.

**spot-bug:** NaN after epoch 1 (LR too high, missing clip); val acc stuck at 50% (data
leak / label shuffle); missing `model.eval()`.

**connect-dots:**
- Kernel trick ↔ Feature maps in quantum computing
- ELBO in VAEs ↔ Rate-distortion theory
- Skip connections ↔ ODE perspective on neural networks
- LoRA ↔ Low-rank approximation of weight updates

---

### Linear Algebra
Eigenvalue computation for 2×2, 3×3 matrices; matrix rank and null space; trace/determinant
properties; unitary/orthogonality verification; tensor products for small systems.

---

### Algorithms & Data Structures
Complexity analysis, correctness for edge cases, algorithm selection justification, recurrence
relations, amortized analysis.

---

### Python / Software Engineering
Mutability gotchas, generator vs list comprehension, decorator behavior, NumPy broadcasting
rules, concurrency pitfalls.
