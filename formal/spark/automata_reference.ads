-- AUTOMATA4/1: standalone SPARK reference, no proof-status claim here.
package Automata_Reference with SPARK_Mode => On is
   subtype Bit is Natural range 0 .. 1;
   subtype Rule_Byte is Natural range 0 .. 255;
   subtype Pattern_Index is Natural range 0 .. 7;
   type Row4 is array (Positive range 1 .. 4) of Bit;

   function Neighborhood (Left, Center, Right : Bit) return Pattern_Index
     with Post => Natural (Neighborhood'Result) =
       4 * Natural (Left) + 2 * Natural (Center) + Natural (Right);

   function Cell (Rule : Rule_Byte; Left, Center, Right : Bit) return Bit
     with Post => Natural (Cell'Result) =
       (Natural (Rule) / (2 ** Natural (Neighborhood (Left, Center, Right)))) mod 2;

   function Step4 (Rule : Rule_Byte; Input : Row4) return Row4
     with Post =>
       Step4'Result (1) = Cell (Rule, 0, Input (1), Input (2))
       and Step4'Result (2) = Cell (Rule, Input (1), Input (2), Input (3))
       and Step4'Result (3) = Cell (Rule, Input (2), Input (3), Input (4))
       and Step4'Result (4) = Cell (Rule, Input (3), Input (4), 0);
end Automata_Reference;
