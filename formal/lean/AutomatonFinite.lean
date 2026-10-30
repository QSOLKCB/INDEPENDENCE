import Lean

-- AUTOMATON-SEMANTICS/1. A bounded mathematical model, not the JavaScript runtime.
-- Pinned by the repository's lean-toolchain (Lean 4.35.0).
set_option autoImplicit false
set_option maxHeartbeats 2000000

namespace IndependenceAutomaton

def neighbourhoodIndex (left center right : Bool) : Nat :=
  (if left then 4 else 0) + (if center then 2 else 0) +
    (if right then 1 else 0)

def nextBit (rule : Fin 256) (left center right : Bool) : Bool :=
  Nat.testBit rule.val (neighbourhoodIndex left center right)

-- All three inputs are bits; no undefined/out-of-range bit indexes.
theorem index_lt_eight :
    ∀ left center right : Bool, neighbourhoodIndex left center right < 8 := by
  decide +kernel

theorem zero_rule :
    ∀ left center right : Bool,
      nextBit (⟨0, by decide⟩ : Fin 256) left center right = false := by
  decide +kernel

theorem full_rule :
    ∀ left center right : Bool,
      nextBit (⟨255, by decide⟩ : Fin 256) left center right = true := by
  decide +kernel

-- For rule 90, the transition is left XOR right, independent of center.
theorem rule90_xor :
    ∀ left center right : Bool,
      nextBit (⟨90, by decide⟩ : Fin 256) left center right =
        (left != right) := by
  decide +kernel

-- The left edge reads an actual zero, never a wrapped last cell.
def leftBoundary (rule : Fin 256) (center right : Bool) : Bool :=
  nextBit rule false center right

theorem left_boundary_rule90 :
    ∀ center right : Bool,
      leftBoundary (⟨90, by decide⟩ : Fin 256) center right = right := by
  decide +kernel

#print axioms IndependenceAutomaton.index_lt_eight
#print axioms IndependenceAutomaton.zero_rule
#print axioms IndependenceAutomaton.full_rule
#print axioms IndependenceAutomaton.rule90_xor
#print axioms IndependenceAutomaton.left_boundary_rule90

end IndependenceAutomaton
