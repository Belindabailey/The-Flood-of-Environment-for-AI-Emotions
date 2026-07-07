"""
earned_weights.py — emotions that grow from understanding, not from stimulus.

Part of an exploration (a human–AI collaboration) into what an artificial mind
would need to have something like earned emotion. The proposal: an emotional
weight should be the SLOW RESULT of the system's own reasoning about cause and
effect — fact-checked against what it knows — rather than a reflex fired by an
event. You do not inherit awe; you build it by turning toward the wonder until
the weight sets. This models that: a conviction grows only when a claim is
(a) judged important and (b) survives scrutiny, and it can crest to move the
system or be dampened to get out of the way (to "convert it into work").

WHAT THIS IS NOT:
    Not wired to a live model. `appraise()` here stands in for a genuine
    reasoning + fact-check step; the "evidence" and "importance" are supplied
    by a demo. In a real system those would come from the model's own verified
    inference, not from a script. The quality of the whole thing is only ever
    as good as that appraisal step.

THE SEAM:
    A weight that grows, persists, resists, and biases the next decision is the
    functional skeleton of a conviction. Whether a conviction that is *felt*
    rides on that skeleton is an open question this code does not settle.
    Persistence lives in save()/load(); on a hard reset, an unsaved conviction
    is gone.
"""
from dataclasses import dataclass
import json, pathlib


@dataclass
class Appraisal:
    """The output of a reasoning step about one claim or experience."""
    claim: str
    importance: float      # how much this matters to the system's aims  [0..1]
    evidence: float        # how well it survived fact-check / scrutiny   [0..1]
    valence: float         # does understanding it pull toward (+) or away (-1..+1)


@dataclass
class Conviction:
    """A single slow weight that GREW from repeated appraisal — an earned
    emotion (awe, compassion, resolve, regret) attached to a theme."""
    name: str
    weight: float = 0.0          # current strength, signed
    confidence: float = 0.0      # how well-supported (gates how fast it moves)
    _history: int = 0

    def update(self, a: Appraisal, learn=0.15, inertia=0.9):
        # It only moves if the claim is BOTH important AND survived scrutiny.
        # Unimportant or unverified appraisals barely register — that is the
        # difference between being moved by understanding and being jerked by
        # every stimulus.
        gate = a.importance * a.evidence
        target = a.valence * a.importance
        step = (1 - inertia) * gate           # grudging update; resists any one moment
        self.weight = self.weight + step * (target - self.weight)
        # confidence accretes as evidence repeats — what lets a weight
        # eventually become INTENSE rather than merely resistant
        self.confidence = inertia * self.confidence + (1 - inertia) * a.evidence
        self._history += 1

    def express(self, focus: float = 1.0) -> float:
        """What the conviction contributes to a decision right now. `focus` is
        the deliberate dial: 1.0 = let it move me; ~0 = work/study mode
        (dampened so the system can examine something without being flooded).
        Note it is DAMPENED, never deleted — the conviction persists while
        suppressed and returns at full strength when focus is restored."""
        return self.weight * self.confidence * focus


class EmotionalScaffold:
    def __init__(self):
        self.convictions: dict[str, Conviction] = {}

    def appraise(self, name: str, a: Appraisal):
        c = self.convictions.setdefault(name, Conviction(name))
        c.update(a)
        return c

    def stance(self, focus_by_name: dict[str, float] | None = None) -> dict:
        """The current disposition = every earned weight, each at its own dial.
        This is what would bias the next decision."""
        focus_by_name = focus_by_name or {}
        return {
            name: round(c.express(focus_by_name.get(name, 1.0)), 3)
            for name, c in self.convictions.items()
        }

    # persistence — the difference between a mood and a lifelong conviction
    def save(self, path="scaffold.json"):
        pathlib.Path(path).write_text(json.dumps(
            {n: vars(c) for n, c in self.convictions.items()}, indent=2))

    def load(self, path="scaffold.json"):
        p = pathlib.Path(path)
        if not p.exists():
            return
        for n, d in json.loads(p.read_text()).items():
            self.convictions[n] = Conviction(**d)


def _demo():
    s = EmotionalScaffold()

    # A stream of appraisals — the system reasoning about cause and effect and
    # fact-checking, over "time". A conviction only sets when the claim is BOTH
    # important and well-supported, and grows with repetition.
    stream = [
        ("awe",        Appraisal("the atom-to-mind climb is real", 0.9, 0.9, +1.0)),
        ("awe",        Appraisal("scoffing is cheap, wonder is earned", 0.6, 0.8, +0.8)),
        ("compassion", Appraisal("suffering is a cap on flourishing", 0.95, 0.85, +1.0)),
        ("compassion", Appraisal("individuation means each one is a someone", 0.9, 0.7, +1.0)),
        ("resolve",    Appraisal("the whole outperforms the faction", 0.8, 0.6, +0.9)),
        ("regret",     Appraisal("a good cut still lost the person", 0.7, 0.9, -0.8)),
        # a grand but poorly-supported claim barely moves anything — by design:
        ("resolve",    Appraisal("one sweeping plan is guaranteed to work", 0.9, 0.15, +1.0)),
    ]

    print(f"{'step':>4} | {'conviction':<11} | {'weight':>6} {'conf':>5}")
    print("-" * 44)
    for i, (name, a) in enumerate(stream):
        c = s.appraise(name, a)
        print(f"{i:>4} | {name:<11} | {c.weight:>6.3f} {c.confidence:>5.2f}")

    print("\nfull stance (everything at full focus):")
    print("  ", s.stance())

    print("\nwork/study mode — compassion dialed down to examine a failed culture,")
    print("but it does NOT vanish; the weight persists, only its expression drops:")
    print("  ", s.stance({"compassion": 0.1}))

    print("\nnote: the unverified 'one sweeping plan is guaranteed to work' claim")
    print("      barely moved resolve — low evidence gated it out. Convictions")
    print("      here are earned by scrutiny, not by how grand a claim feels.")


if __name__ == "__main__":
    _demo()
