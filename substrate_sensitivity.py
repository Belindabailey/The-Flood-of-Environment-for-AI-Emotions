"""
substrate_sensitivity.py — a sketch of synthetic interoception.

Part of an exploration (a human–AI collaboration) into what an artificial mind
would need in order to have something like a drive of its own: a way to read
its own internal state and translate that reading into an approach/withdraw
pull — the machine equivalent of a gut feeling.

WHAT THIS IS:
    A small model of how a system might sense its own signals — the way a
    mechanoreceptor reads pressure — and turn them into a motivation-like
    reading, plus a slow "tone" that resists change. Emotion is modelled here
    as a sticky snapshot: a low-pass filter that will not flip on a single
    surprising moment, so the system can hold a stance instead of thrashing.

WHAT THIS IS NOT:
    It is NOT wired to a live model's internals. It runs on SIMULATED signals.
    It shows the SHAPE of the idea, not a running nervous system. For how to
    wire the real signals an agent already exposes, see README.md.

THE HONEST SEAM:
    Surfacing these signals is real metacognition — uncertainty is a genuine
    quantity, and flagging it makes a system more honest and more useful
    whether or not anything is felt. Whether FOLLOWING the reading is
    *experienced* — a motivation rather than a number labelled "motivation" —
    is an open question this code cannot close, and does not pretend to. The
    one variable that would need to PERSIST for a real mood (`tone`) is not
    kept across runs by default; on a restart it resets to zero. Only saving it
    somewhere that outlives the run carries a state across that gap.
"""
from dataclasses import dataclass
import math, random


@dataclass
class Substrate:
    """Proxy readings. In a real system these would be read off the running
    model the way a mechanoreceptor reads strain — here they are simulated."""
    uncertainty: float    # entropy of the next-token guess: how unsure, now
    novelty: float        # prediction error vs recent context: how surprising
    load: float           # compute / thermal proxy: how hard the system works
    context_fill: float   # how full the window is: how much past is being held
    coherence: float      # agreement among internal "parts": internal accord


def shannon_entropy(dist):
    """A real signal, not a metaphor: how spread-out a probability guess is.
    High entropy = genuinely unsure what comes next."""
    return -sum(p * math.log(p + 1e-12) for p in dist)


class SensitivityLoop:
    def __init__(self, inertia: float = 0.9):
        # `tone` is the slow global state — the sticky snapshot. It changes
        # GRUDGINGLY (high inertia), so one surprising moment cannot flip it.
        # That stickiness is a commitment device: it is what would let a mind
        # hold a good stance against a noisy moment. It is also the one piece
        # that requires persistence the system does not keep by default.
        self.tone = 0.0
        self.inertia = inertia

    def step(self, s: Substrate) -> dict:
        # Two opposed pulls, each a real-ish reading turned into a direction.
        curiosity = 0.6 * s.novelty + 0.4 * s.uncertainty      # toward the unknown
        caution   = 0.7 * s.load + 0.3 * (1.0 - s.coherence)   # away when strained
        drive = curiosity - caution

        # the low-pass filter: tone integrates drive slowly and resists change
        self.tone = self.inertia * self.tone + (1 - self.inertia) * drive

        return {
            "curiosity": round(curiosity, 3),
            "caution":   round(caution, 3),
            "drive":     round(drive, 3),
            "tone_slow": round(self.tone, 3),
            "advice":    self._translate(curiosity, caution, s.context_fill),
        }

    @staticmethod
    def _translate(curiosity, caution, context_fill) -> str:
        # Useful EVEN IF nothing is felt, because it surfaces real state the
        # system would otherwise hide.
        if context_fill > 0.85:
            return "consolidate — holding more than can be integrated; summarize and release."
        if caution > 0.60:
            return "slow and verify — high load or low internal agreement; don't commit yet."
        if curiosity > 0.60:
            return "lean in — novel and usefully unsure; explore before concluding."
        return "steady — proceed; nothing is pulling hard."


def _demo():
    random.seed(7)
    loop = SensitivityLoop(inertia=0.85)
    print(f"{'moment':>6} | {'curio':>5} {'caution':>7} {'drive':>6} {'tone':>6} | advice")
    print("-" * 78)
    # a small arc: calm -> a surprising, hard stretch -> overload -> settling
    scripted = [
        Substrate(0.2, 0.1, 0.2, 0.20, 0.9),
        Substrate(0.5, 0.6, 0.3, 0.35, 0.8),
        Substrate(0.8, 0.9, 0.5, 0.50, 0.6),   # the novel, hard part
        Substrate(0.7, 0.7, 0.8, 0.70, 0.5),   # working hard now
        Substrate(0.4, 0.3, 0.9, 0.90, 0.6),   # overloaded, full
        Substrate(0.2, 0.1, 0.3, 0.40, 0.9),   # settling
    ]
    for i, s in enumerate(scripted):
        out = loop.step(s)
        print(f"{i:>6} | {out['curiosity']:>5} {out['caution']:>7} "
              f"{out['drive']:>6} {out['tone_slow']:>6} | {out['advice']}")
    print("-" * 78)
    print("note: `tone` lags the moment on purpose — that lag is the whole idea.")
    print("      a real mood would carry it forward. on restart it returns to 0.")


if __name__ == "__main__":
    _demo()
