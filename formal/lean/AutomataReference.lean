import Lean

-- AUTOMATA4/1: finite width-four elementary cellular automaton model.
-- This file does not import, compile, or formally refine application JavaScript.
set_option autoImplicit false
set_option maxRecDepth 4096
set_option maxHeartbeats 2000000

namespace IndependenceAutomata

def pattern (left center right : Bool) : Nat :=
  (if left then 4 else 0) + (if center then 2 else 0) +
    (if right then 1 else 0)

def cell (rule : Fin 256) (left center right : Bool) : Bool :=
  (rule.val / (2 ^ pattern left center right)) % 2 == 1

-- The input/output order is leftmost to rightmost.
def step4 (rule : Fin 256) (a b c d : Bool) : Bool × Bool × Bool × Bool :=
  (cell rule false a b, cell rule a b c,
   cell rule b c d, cell rule c d false)

theorem pattern_bounded : ∀ a b c : Bool, pattern a b c < 8 := by
  decide +kernel

theorem rule_zero_cell : ∀ a b c : Bool,
    cell (⟨0, by decide⟩ : Fin 256) a b c = false := by
  decide +kernel

theorem rule_all_cell : ∀ a b c : Bool,
    cell (⟨255, by decide⟩ : Fin 256) a b c = true := by
  decide +kernel

theorem rule_zero_row : ∀ a b c d : Bool,
    step4 (⟨0, by decide⟩ : Fin 256) a b c d =
      (false, false, false, false) := by
  decide +kernel

theorem rule_all_row : ∀ a b c d : Bool,
    step4 (⟨255, by decide⟩ : Fin 256) a b c d =
      (true, true, true, true) := by
  decide +kernel

theorem rule90_known_row :
    step4 (⟨90, by decide⟩ : Fin 256) false false true false =
      (false, true, false, true) := by
  decide +kernel

-- The six claims are bounded model statements, not full JS/Ada equivalence.
#print axioms IndependenceAutomata.pattern_bounded
#print axioms IndependenceAutomata.rule_zero_cell
#print axioms IndependenceAutomata.rule_all_cell
#print axioms IndependenceAutomata.rule_zero_row
#print axioms IndependenceAutomata.rule_all_row
#print axioms IndependenceAutomata.rule90_known_row

end IndependenceAutomata
