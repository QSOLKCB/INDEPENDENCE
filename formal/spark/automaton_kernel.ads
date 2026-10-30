-- AUTOMATON-SEMANTICS/1. Only this pure package is under SPARK analysis.
package Automaton_Kernel with SPARK_Mode => On is
   type Bit is mod 2;
   subtype Rule_Type is Natural range 0 .. 255;

   function Next_Bit (Rule : Rule_Type; Left, Center, Right : Bit)
      return Bit
   with
      Post => Natural (Next_Bit'Result) =
        (Natural (Rule) /
           (2 ** (4 * Natural (Left) + 2 * Natural (Center)
                  + Natural (Right)))) mod 2;
end Automaton_Kernel;
