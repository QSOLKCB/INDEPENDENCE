(* AUTOMATA-LIST/1: independent finite-list automaton semantics.
   Model-level results only: NOT a refinement proof of Ada/Lean/JavaScript.
   Pin Rocq 9.2.0. No axioms, admits, opaque assumptions, or external plugins. *)
From Stdlib Require Import List Bool Arith Lia.
Import ListNotations.

Module IndependenceRocq.

Definition neighborhood (left center right : bool) : nat :=
  (if left then 4 else 0) +
  (if center then 2 else 0) +
  (if right then 1 else 0).

Definition rule_bit (rule index : nat) : bool :=
  Nat.eqb ((rule / 2 ^ index) mod 2) 1.

(* Arithmetic interpretation of Wolfram's eight rule bits. *)
Definition arithmetic_cell (rule : nat) (left center right : bool) : bool :=
  rule_bit rule (neighborhood left center right).

(* Independent, explicit pattern-table interpretation. *)
Definition table_cell (rule : nat) (left center right : bool) : bool :=
  match left, center, right with
  | false, false, false => rule_bit rule 0
  | false, false, true  => rule_bit rule 1
  | false, true, false  => rule_bit rule 2
  | false, true, true   => rule_bit rule 3
  | true, false, false  => rule_bit rule 4
  | true, false, true   => rule_bit rule 5
  | true, true, false   => rule_bit rule 6
  | true, true, true    => rule_bit rule 7
  end.

(* The initial left neighbour is zero; exterior right neighbour is zero.
   The recursive left variable always refers to PRE-STEP input, so the
   update is simultaneous. Empty rows and singleton rows are defined. *)
Fixpoint arithmetic_step (rule : nat) (left : bool) (row : list bool)
    : list bool :=
  match row with
  | [] => []
  | center :: rest =>
      arithmetic_cell rule left center (hd false rest)
      :: arithmetic_step rule center rest
  end.

Fixpoint table_step (rule : nat) (left : bool) (row : list bool)
    : list bool :=
  match row with
  | [] => []
  | center :: rest =>
      table_cell rule left center (hd false rest)
      :: table_step rule center rest
  end.

Fixpoint xor_step (left : bool) (row : list bool) : list bool :=
  match row with
  | [] => []
  | center :: rest =>
      xorb left (hd false rest) :: xor_step center rest
  end.

Definition step (rule : nat) (row : list bool) : list bool :=
  arithmetic_step rule false row.

Definition step4 (rule : nat) (a b c d : bool) : list bool :=
  [arithmetic_cell rule false a b;
   arithmetic_cell rule a b c;
   arithmetic_cell rule b c d;
   arithmetic_cell rule c d false].

Theorem neighborhood_bounded : forall a b c,
  neighborhood a b c < 8.
Proof.
  intros [] [] []; unfold neighborhood; simpl; lia.
Qed.

Theorem arithmetic_table_cell : forall rule a b c,
  arithmetic_cell rule a b c = table_cell rule a b c.
Proof.
  intros rule [] [] []; reflexivity.
Qed.

Theorem arbitrary_width_length : forall rule left row,
  length (arithmetic_step rule left row) = length row.
Proof.
  intros rule left row; revert left.
  induction row as [| center rest IH]; intro left; simpl.
  - reflexivity.
  - now rewrite IH.
Qed.

Theorem arbitrary_width_table_length : forall rule left row,
  length (table_step rule left row) = length row.
Proof.
  intros rule left row; revert left.
  induction row as [| center rest IH]; intro left; simpl.
  - reflexivity.
  - now rewrite IH.
Qed.

(* Mathematical equivalence of both independently defined row evaluators. *)
Theorem independent_models_equivalent : forall rule left row,
  arithmetic_step rule left row = table_step rule left row.
Proof.
  intros rule left row; revert left.
  induction row as [| center rest IH]; intro left; simpl.
  - reflexivity.
  - rewrite arithmetic_table_cell. rewrite IH. reflexivity.
Qed.

Theorem rule_zero_cell : forall a b c,
  arithmetic_cell 0 a b c = false.
Proof.
  intros [] [] []; reflexivity.
Qed.

Theorem rule_255_cell : forall a b c,
  arithmetic_cell 255 a b c = true.
Proof.
  intros [] [] []; reflexivity.
Qed.

Theorem rule_zero_all_widths : forall left row,
  arithmetic_step 0 left row = repeat false (length row).
Proof.
  intros left row; revert left.
  induction row as [| center rest IH]; intro left; simpl.
  - reflexivity.
  - rewrite rule_zero_cell. rewrite IH. reflexivity.
Qed.

Theorem rule_255_all_widths : forall left row,
  arithmetic_step 255 left row = repeat true (length row).
Proof.
  intros left row; revert left.
  induction row as [| center rest IH]; intro left; simpl.
  - reflexivity.
  - rewrite rule_255_cell. rewrite IH. reflexivity.
Qed.

Theorem rule90_cell_xor : forall left center right,
  arithmetic_cell 90 left center right = xorb left right.
Proof.
  intros [] [] []; reflexivity.
Qed.

Theorem rule90_all_widths : forall left row,
  arithmetic_step 90 left row = xor_step left row.
Proof.
  intros left row; revert left.
  induction row as [| center rest IH]; intro left; simpl.
  - reflexivity.
  - rewrite rule90_cell_xor. rewrite IH. reflexivity.
Qed.

(* This is a width-four model bridge, not an executable JS refinement. *)
Theorem automata4_model_bridge : forall rule a b c d,
  step rule [a; b; c; d] = step4 rule a b c d.
Proof.
  intros; reflexivity.
Qed.

Theorem zero_boundary_empty : forall rule,
  step rule [] = [].
Proof.
  intro rule; reflexivity.
Qed.

Theorem zero_boundary_singleton : forall rule a,
  step rule [a] = [arithmetic_cell rule false a false].
Proof.
  intros; reflexivity.
Qed.

Example rule90_known_four :
  step 90 [false; false; true; false] =
  [false; true; false; true].
Proof. reflexivity. Qed.

(* The compiler must print no "Axioms:" lines for EACH named theorem.
   These reports and a compiled .vo are valid only after real Rocq execution. *)
Print Assumptions neighborhood_bounded.
Print Assumptions arithmetic_table_cell.
Print Assumptions arbitrary_width_length.
Print Assumptions arbitrary_width_table_length.
Print Assumptions independent_models_equivalent.
Print Assumptions rule_zero_cell.
Print Assumptions rule_255_cell.
Print Assumptions rule_zero_all_widths.
Print Assumptions rule_255_all_widths.
Print Assumptions rule90_cell_xor.
Print Assumptions rule90_all_widths.
Print Assumptions automata4_model_bridge.
Print Assumptions zero_boundary_empty.
Print Assumptions zero_boundary_singleton.
Print Assumptions rule90_known_four.

End IndependenceRocq.
