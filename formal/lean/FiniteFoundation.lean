import Lean

-- A development-only mathematical model. No FFI, native evaluation,
-- compiler-generated executable or dependency on application code.
set_option autoImplicit false
set_option maxRecDepth 4096
set_option maxHeartbeats 2000000

namespace IndependenceLean

/-- CRT for the specific coprime pair (2, 3). This does not assert general CRT. -/
def crtEncode (n : Fin 6) : Fin 2 × Fin 3 :=
  (⟨n.val % 2, Nat.mod_lt _ (by decide)⟩,
   ⟨n.val % 3, Nat.mod_lt _ (by decide)⟩)

/-- 3 ≡ 1 mod 2 and 4 ≡ 1 mod 3; both cancel the other residue. -/
def crtDecode (p : Fin 2 × Fin 3) : Fin 6 :=
  ⟨(3 * p.1.val + 4 * p.2.val) % 6, Nat.mod_lt _ (by decide)⟩

theorem crt_left_inverse : ∀ n : Fin 6, crtDecode (crtEncode n) = n := by
  decide +kernel

theorem crt_right_inverse : ∀ p : Fin 2 × Fin 3, crtEncode (crtDecode p) = p := by
  decide +kernel

/-- GF(2) reference semantics represented by Bool, not an Ada/Python proof. -/
def parityAdd (a b : Bool) : Bool := Bool.xor a b
def parityMul (a b : Bool) : Bool := Bool.and a b

theorem gf2_add_comm : ∀ a b : Bool, parityAdd a b = parityAdd b a := by
  decide +kernel

theorem gf2_add_assoc :
    ∀ a b c : Bool, parityAdd (parityAdd a b) c = parityAdd a (parityAdd b c) := by
  decide +kernel

theorem gf2_add_self : ∀ a : Bool, parityAdd a a = false := by
  decide +kernel

theorem gf2_mul_comm : ∀ a b : Bool, parityMul a b = parityMul b a := by
  decide +kernel

theorem gf2_left_distrib :
    ∀ a b c : Bool,
      parityMul a (parityAdd b c) =
        parityAdd (parityMul a b) (parityMul a c) := by
  decide +kernel

/-- Ternary cyclic phase model is Z/3Z, not a quantum qutrit proof. -/
def phaseAdd (a b : Fin 3) : Fin 3 :=
  ⟨(a.val + b.val) % 3, Nat.mod_lt _ (by decide)⟩

theorem phase_add_comm : ∀ a b : Fin 3, phaseAdd a b = phaseAdd b a := by
  decide +kernel

theorem phase_add_assoc :
    ∀ a b c : Fin 3,
      phaseAdd (phaseAdd a b) c = phaseAdd a (phaseAdd b c) := by
  decide +kernel

theorem phase_zero : ∀ a : Fin 3, phaseAdd a ⟨0, by decide⟩ = a := by
  decide +kernel

/-- Degree-lex comparison on *unbounded* exponent pairs. -/
def monomialLt (a b : Nat × Nat) : Prop :=
  a.1 + a.2 < b.1 + b.2 ∨
    (a.1 + a.2 = b.1 + b.2 ∧ a.1 < b.1)

theorem monomial_irrefl (a : Nat × Nat) : ¬ monomialLt a a := by
  unfold monomialLt
  omega

theorem monomial_trans (a b c : Nat × Nat) :
    monomialLt a b → monomialLt b c → monomialLt a c := by
  intro hab hbc
  unfold monomialLt at *
  rcases hab with hlt | ⟨heq, hlex⟩
  · rcases hbc with hlt' | ⟨heq', hlex'⟩
    · left; omega
    · left; omega
  · rcases hbc with hlt' | ⟨heq', hlex'⟩
    · left; omega
    · right; constructor <;> omega

theorem monomial_translate (a b shift : Nat × Nat) :
    monomialLt a b →
      monomialLt (a.1 + shift.1, a.2 + shift.2)
                 (b.1 + shift.1, b.2 + shift.2) := by
  intro hab
  unfold monomialLt at *
  rcases hab with hlt | ⟨heq, hlex⟩
  · left; omega
  · right; constructor <;> omega

-- No unbounded well-foundedness or trichotomy theorem is claimed by this file.
-- Every declared theorem receives a transitive dependency audit:
#print axioms IndependenceLean.crt_left_inverse
#print axioms IndependenceLean.crt_right_inverse
#print axioms IndependenceLean.gf2_add_comm
#print axioms IndependenceLean.gf2_add_assoc
#print axioms IndependenceLean.gf2_add_self
#print axioms IndependenceLean.gf2_mul_comm
#print axioms IndependenceLean.gf2_left_distrib
#print axioms IndependenceLean.phase_add_comm
#print axioms IndependenceLean.phase_add_assoc
#print axioms IndependenceLean.phase_zero
#print axioms IndependenceLean.monomial_irrefl
#print axioms IndependenceLean.monomial_trans
#print axioms IndependenceLean.monomial_translate

end IndependenceLean
