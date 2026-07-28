# The working discipline

This is the operating half of a method for building precise things with a model. The instruments are already in your hands: the coordination suite and Frame Language servers you are running expose thirteen tools, and wherever this document needs a definition, a checklist or an instrument, it names the call rather than reproducing it. What is written here is the part that is not callable.

Install or update both servers before you start. They are published on JSR as `@proof-of-coord/structural-integrity` and `@proof-of-coord/frame-language`, and `deno run -A jsr:` followed by either name starts it. They changed substantially on 27 July 2026. They now validate every argument and return a readable error naming the argument rather than a raw protocol failure, every response declares which standard version produced it, and the standard links `list_standards` hands out were all returning 404 until that afternoon because standard filenames carry versions and every file had moved. An older copy will hand you dead links and versions up to two minor releases behind.

---

## Part one: the epistemic engine

Four moves. They only work together, and the fourth is the one people skip.

### Triangulation, not eclecticism

Frameworks from different disciplines are not collected and combined. They are recognised as independently convergent. When several frameworks, developed by people who never met, at different scales and in different registers, land on the same structural claim, that convergence is better evidence the structure is real than any single authority could give you.

Eclecticism assembles frameworks for coverage. This triangulates toward a reality the frameworks are all instances of. The wheel being reinvented keeps turning out to be round, and the roundness is the finding, not the wheel.

### Disconfirmation, which is what makes convergence mean anything

A convergence is only evidence if the inquiry was structured to miss it. That is the whole of it. If you organised the work to find confirmation, resonance can always be found, and the convergence proves nothing. If you organised it around disconfirmation, by thinking in opposites, by stating falsifiability conditions before you look, by actively constructing the cases that would break the claim, then an unexpected convergence carries real weight.

There is a distinction here that is easy to collapse. Openness to being wrong when disconfirmation arrives is receptivity, and it is necessary. Constructing the test before the result arrives is discipline, and it is different. Neither substitutes for the other.

The reframe worth carrying: disconfirmation is a growth engine rather than a defensive filter. Each encounter with something that could have broken a construct either sharpens it or shows it holds under that specific pressure. Confirmation tells you the frame fits a case. Disconfirmation tells you what the frame is made of.

### Sustained curiosity, the condition prior to disconfirmation

Disconfirmation already operates inside a frame: you have a claim, you test it, you know roughly what level the test runs at. Bringing in material from outside is prior to that. It is not disconfirmation, it is maintenance of the capacity to be surprised at all, which is what disconfirmation needs in order to function. Without it, disconfirmation becomes a technique applied to a narrowing field.

The diagnostic is unmistakable once you know it. **When the architecture starts to feel complete, that is the signal this condition is degrading.** Work then proliferates outward inside a closed system, more documents, more applications, more elaboration, generating without surprise.

Two properties keep the contact real. Material comes in without a hypothesis about where it will land, because the contact itself reveals which level it hits, and filtering entry to "things that might disconfirm X" excludes exactly the material that would have hit at a level X never anticipated. And the commitment behind it runs two ways: an actual conviction that you have not thought of everything, and a refusal to keep generating only your own thinking however good it is.

### Concrete cases force precision

The significant advances come from contact with specific real events, not from abstract work. A particular failure, a particular attack, a particular dataset. These are not illustrations of principles you already hold. They are the friction that forces a principle into precision, and the abstraction has to arrive after the case. When the case is absent the principle floats. When it is present the principle lands.

This is the opposite of starting with a principle and deriving applications.

---

## Part two: working with a model

### The sequence, and why it is structural rather than preferred

Read this one first if you read only one.

Work in three steps and in this order. **Synthesis**, where you hold the whole before analysis begins and run cross-domain recognition. **Formulation**, where that whole view sharpens into a resolvable question. **Concretion**, where the formulated question goes to the tool.

The reason is not that it produces nicer results. The tool stack is Complicated-domain by construction. Scripts execute settled patterns. Language models are trained on expert distributions to approximate discriminative judgment inside a known domain. When a situation departs from that distribution the model does not perceive the shift into Complex territory; it goes on producing Complicated-domain outputs for Complex-domain inputs. That is not random error, it is structural misclassification, and it looks like an answer.

Skills crystallise expert pathways. Memory and MCP servers deepen the same architecture. Each is a real improvement and each remains capped at Complicated.

So handing a model a Complex-domain question directly gets you Complicated-domain output that appears to answer it. The sequence prevents that by having you work first in the domain the tools cannot reach, and hand over only once the question has a shape the tool can be correctly calibrated to.

**Why a designed sequence is permitted, and on what condition.** A reader arriving from the Sensemaking Standard will notice that an ordered set of steps looks like the thing that standard rules out. Section 9.6 is where the line falls, and it sorts the standard into layers. The five structural invariants, the three scales, the three action invariants and the three named structural assumptions are constitutive: no adopting party may change them. The specific practices adopted to satisfy the invariants are mutable. Any sequence may be designed. What may not be redesigned is what counts as sensemaking.

The permission is conditional, and the condition is the part that is easy to lose. This order is about which question reaches the tool. It is not a claim that understanding finishes before action starts. Invariant 3.3 names a process that prohibits action until understanding is complete as analysis paralysis, and Invariant 3.4 puts the stopping point at sufficiency rather than completeness: a frame good enough to act on with a named path for revising it, reached before every open question is closed. Held as written, the sequence satisfies both, because Concretion generates the information that sends you back through the first two steps and the loop is the point. Hardened into a rule that nothing may be built until the first two steps are finished, it violates both. One further guard, from Invariant 3.1: a process that runs because it is the workflow rather than because something stopped making sense is compliance. Running these three steps is not itself sensemaking and does not become sensemaking by being followed.

Call `lookup_three_frames` for the frame vocabulary this rests on.

### Care as method, or why one pass is never enough

Precision and non-harming are one commitment with two constitutive aspects, not two principles held in balance against each other. Naming them separately is how you see the two directions the single commitment fails in, and each aspect is fully operative in the same frame rather than trading against the other.

Under-correction is the first direction. Every instance that should change must change, because incompleteness in a coherent corpus propagates: what is left uncorrected becomes a source of drift that later work compounds without knowing where it came from. Precision left undone is where the harm lands.

Over-correction is the second. Not everything that resembles the target is the target. Changing the wrong instance distorts the argument, and knowing when not to change is as demanding as knowing what to change.

Both are failures of the same thing, which is why correcting for one without attending to the other reliably produces the other. Neither direction is closed off in a single pass from a single angle. A string search finds too much. A close reading of a bounded set misses the scope. Multiple passes from different angles are what the commitment looks like in practice, and the per-instance judgment cannot be automated because it requires reading the argument the use sits inside.

One practical consequence: that judgment is more reliably made when attention is fresh and scope is bounded than in one long comprehensive sweep.

### Specification inheritance, and why the mistake is invisible

Precision produces findings faster than the structure can absorb them. When an architectural finding is clear, there is a pull to specify it at the implementation level before checking that the level above it is settled.

The damage is that implementation specificity creates path dependency. The next session reads the spec and builds from it rather than questioning it, assumptions compound, and the mistake never appears as a mistake. It appears as settled ground.

Two checks before writing anything downstream. Is the frame it rests on recorded as provisional, with its revision conditions stated and the questions left unpursued named, since open questions are not a bar to building but unnamed ones are: what goes unrecorded reads as absent to whoever builds next. And is it in the right document type, because a sensemaking capture and a standard both carry structural content and have different normative status. Both must hold: correct content in the wrong document type is not sufficient, and a frame at the wrong level is not sufficient.

The line worth remembering: the pressure to build is the signal that the finding is real. The discipline is to route it before building.

For the under- and over-specification failure modes at each level, call `lookup_corollary`.

---

## Part three: two standing tools

### The Johansson Blocks method

Identify a physical precision problem that was solved at the foundational level. Analyse the structural logic of the solution. Apply that logic to the analogous foundational problem in your own domain.

This is not analogy-drawing. It is structural isomorphism. The physical solution was correct because the physics required it, and the logic that made it correct does not belong to physics, it belongs to the problem class. When the same problem class appears elsewhere, the same logic applies.

The source case: Carl Edvard Johansson faced factories with no shared measurement reference, so parts were not interchangeable. His solution had three moves. A foundational reference derived from first principles, the surface plate, bootstrapped from three imperfect surfaces ground against each other until the only plane all three share is the one that is actually flat. A standard unit made combinable and portable, the gauge blocks. And a traceability chain certifying any measurement back to the primary reference.

That bootstrapping move is worth its own attention, because it needs no prior reference. Three imperfect things correcting each other produce the standard. You can build a foundational reference out of mutual correction rather than external authority.

Carry the four preconditions as a standing question. Any domain attempting precision at scale needs a foundational reference derived from first principles, an agreed unit of measure, portable combinable standards that put the unit in practitioners' hands, and a traceability authority maintaining the chain back. When you meet such a domain, ask which of the four are present and which are missing. The absent one usually explains the failure.

### Correct words without the architecture

Vocabulary can be right while the structure it names is absent, and the vocabulary then conceals the absence rather than revealing it. A document can be expressed entirely in the correct terms and fail to function as what those terms describe.

This is one of eight named ways that happens. Call `frame2_functioning_check` for all eight, each with the falsifiability variant that tells you how to detect it. It is the most useful single call on either server for auditing your own writing, because it catches the failure that reads as success.

For the vocabulary itself, `check_watchlist` takes a term and `audit_text` scans a passage.

---

## A closing note on partiality

Every specification is a perspective, and taking a perspective is what degrades the thing it was taken on. Each angle is accurate. But in the act of selecting one, the full simultaneous reality is no longer what you are holding.

This is not a failure to fix. It is the condition under which all specification happens. The practical consequence is modest and worth stating: a document is partial by construction, so treat completeness as a direction rather than a state, and expect the next contact from outside to show you which part you were standing on.
