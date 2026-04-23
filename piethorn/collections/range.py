from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


def combine_slices(slice1: slice, slice2: slice, max_len: int) -> slice:
    """
    Creates a new slice from two slices.

    The new slice will do the same as `a_list[slice1][slice2]`.

    :param max_len: The maximum length of the new slice.
    :param slice1: The first slice, this is the base.
    :param slice2: The second slice, this is applied to slice1.
    :return: A new slice where slice2 is applied to slice1.
    """
    r1 = range(*slice1.indices(max_len))
    r2 = r1[slice2]
    return slice(r2.start, r2.stop, r2.step)

class SliceMode(Enum):
    """Describe how safely a slice can be composed without sequence length."""

    POSITIVE = auto()
    NEGATIVE = auto()
    POSITIVE_HEURISTIC = auto()
    NEGATIVE_HEURISTIC = auto()
    HEURISTIC = auto()
    AMBIGUOUS = auto()

    @staticmethod
    def classify_one(s: slice) -> "SliceMode":
        """Classify one slice by how dependent it is on sequence length."""
        start = s.start
        stop = s.stop

        # Fully open slice (::k)
        if start is None and stop is None:
            return SliceMode.HEURISTIC

        # One side missing → heuristic but directional if possible
        if start is None or stop is None:
            if (start is not None and start < 0) or (stop is not None and stop < 0):
                return SliceMode.NEGATIVE_HEURISTIC
            if (start is not None and start >= 0) or (stop is not None and stop >= 0):
                return SliceMode.POSITIVE_HEURISTIC
            return SliceMode.HEURISTIC

        # Both concrete
        if start >= 0 and stop >= 0:
            return SliceMode.POSITIVE
        if start < 0 and stop < 0:
            return SliceMode.NEGATIVE

        # Mixed-sign concrete bounds are inherently length-dependent
        return SliceMode.AMBIGUOUS

    @staticmethod
    def classify(s1: slice, s2: Optional[slice]=None) -> SliceMode | tuple[SliceMode, SliceMode, SliceMode]:
        """Classify one or two slices and their combined composition mode."""
        m1 = SliceMode.classify_one(s1)

        if s2 is None:
            return m1

        m2 = SliceMode.classify_one(s2)

        # Strong rule: ambiguity propagates
        if SliceMode.AMBIGUOUS in (m1, m2):
            combined = SliceMode.AMBIGUOUS

        # Both exact negative → exact negative
        elif m1 is SliceMode.NEGATIVE and m2 is SliceMode.NEGATIVE:
            combined = SliceMode.NEGATIVE

        # Both exact positive → exact positive
        elif m1 is SliceMode.POSITIVE and m2 is SliceMode.POSITIVE:
            combined = SliceMode.POSITIVE

        # Any negative influence → negative heuristic
        elif (
                m1 in (SliceMode.NEGATIVE, SliceMode.NEGATIVE_HEURISTIC)
                or m2 in (SliceMode.NEGATIVE, SliceMode.NEGATIVE_HEURISTIC)
        ):
            combined = SliceMode.NEGATIVE_HEURISTIC

        # Any positive influence → positive heuristic
        elif (
                m1 in (SliceMode.POSITIVE, SliceMode.POSITIVE_HEURISTIC)
                or m2 in (SliceMode.POSITIVE, SliceMode.POSITIVE_HEURISTIC)
        ):
            combined = SliceMode.POSITIVE_HEURISTIC

        else:
            combined = SliceMode.HEURISTIC

        return m1, m2, combined


@dataclass(frozen=True)
class SliceComposeResult:
    """Hold the result of composing two slices and its confidence metadata."""

    slice: slice
    exact: bool
    mode: SliceMode

def is_full_slice(s: slice):
    """Return ``True`` when a slice leaves both bounds open."""

    return s.start is None and s.stop is None

def adhoc_combine_slices(s1: slice, s2: slice) -> SliceComposeResult:
    """
    Best-effort composition of two slices without knowing sequence length.

    Intended meaning:
        seq[adhoc_combine_slices(s1, s2)]  ~  seq[s1][s2]

    This is only reliable when the slices are already effectively normalized,
    or when omitted bounds do not matter to the final result.

    It is NOT generally correct.

    :param s1: The first slice, this is the base.
    :param s2: The second slice, this is applied to s1.
    :return: A new slice where s2 is applied to s1.
    """
    step1 = 1 if s1.step is None else s1.step
    step2 = 1 if s2.step is None else s2.step

    if step1 == 0 or step2 == 0:
        raise ValueError("slice step cannot be zero")

    mode1, mode2, mode = SliceMode.classify(s1, s2)

    # 1) Exact case: s1 is a full forward slice, i.e. seq[::step1]
    # This is the progression 0, step1, 2*step1, ...
    # We cannot know the finite stop without n when s2.stop is None,
    # but we can still compose the start/step exactly.
    if s1.start is None and s1.stop is None and step1 > 0:
        start = None if s2.start is None else s2.start * step1
        stop = None if s2.stop is None else s2.stop * step1
        out = slice(start, stop, step1 * step2)
        return SliceComposeResult(out, True, mode)

    def compose_progression(base_start: int, base_stop: int, base_step: int, sub: slice) -> slice:
        # local location
        if base_step > 0:
            m = 0 if base_start >= base_stop else (base_stop - base_start + base_step - 1) // base_step
        else:
            step_abs = -base_step
            m = 0 if base_start <= base_stop else (base_start - base_stop + step_abs - 1) // step_abs

        # Normalize s2 against the locally known length m.
        a2, b2, c2 = sub.indices(m)
        k = len(range(a2, b2, c2))

        if k == 0:
            return slice(0, 0, 1)

        start = base_start + a2 * base_step
        step = base_step * c2
        stop = start + step * k
        return slice(start, stop, step)

    # 2) Exact case: s1 is concrete forward-bounded
    if mode1 is SliceMode.POSITIVE:
        out = compose_progression(s1.start, s1.stop, step1, s2)
        return SliceComposeResult(out, True, mode1)

    # 3) Exact case: s1 is concrete negative-bounded
    if mode1 is SliceMode.NEGATIVE:
        # Convert negative coordinates to end-relative offsets.
        # Example: -1 -> 0, -2 -> 1, -8 -> 7
        off_start = -s1.start - 1
        off_stop = -s1.stop - 1

        # In offset space, increasing offset means farther from the end.
        # Original negative progression:
        #   value = ..., -8, -6, -4 ...
        # offset progression:
        #   7, 5, 3 ...
        # so the step flips sign.
        off_step = -step1

        out = compose_progression(off_start, off_stop, off_step, s2)

        if out == slice(0, 0, 1):
            return SliceComposeResult(out, True, mode1)

        start_off = out.start
        stop_off = out.stop
        step_off = out.step

        # Convert offsets back to negative coordinates.
        # offset 0 -> -1, offset 1 -> -2, offset 7 -> -8
        start = -(start_off + 1)
        stop = -(stop_off + 1)
        step = -step_off

        return SliceComposeResult(
            slice(start, stop, step),
            True,
            mode1,
        )

    # Heuristic fallback.
    step = step1 * step2

    # 4) Heuristic fallback: If s1 start is concrete, we can still map relative positions from s2.
    if s1.start is not None:
        start = s1.start if s2.start is None else s1.start + s2.start * step1
        stop = None if s2.stop is None else s1.start + s2.stop * step1
        return SliceComposeResult(
            slice(start, stop, step),
            False,
            mode,
        )

    # Identity-ish cases.
    # 5) Heuristic identity-ish simplifications

    # If s2 is the identity slice, just return s1 normalized for missing step.
    if s2.start is None and s2.stop is None and step2 == 1:
        return SliceComposeResult(
            slice(s1.start, s1.stop, step1),
            False,
            mode1,
        )

    # If s1 is the identity slice, return s2 normalized for missing step.
    if s1.start is None and s1.stop is None and step1 == 1:
        return SliceComposeResult(
            slice(s2.start, s2.stop, step2),
            False,
            mode2,
        )

    # Fully ambiguous fallback.
    return SliceComposeResult(
            slice(None, None, step),
            False,
            SliceMode.AMBIGUOUS,
        )

def slice_len(slice1: slice, max_len: int):
    """Return the concrete length of a slice for a sequence of ``max_len``."""

    return len(range(*slice1.indices(max_len)))
