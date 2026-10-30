package body Automata_Reference with SPARK_Mode => On is
   function Neighborhood (Left, Center, Right : Bit) return Pattern_Index is
   begin
      return Pattern_Index
        (4 * Natural (Left) + 2 * Natural (Center) + Natural (Right));
   end Neighborhood;

   function Cell (Rule : Rule_Byte; Left, Center, Right : Bit) return Bit is
      Index : constant Pattern_Index := Neighborhood (Left, Center, Right);
   begin
      return Bit ((Natural (Rule) / (2 ** Natural (Index))) mod 2);
   end Cell;

   function Step4 (Rule : Rule_Byte; Input : Row4) return Row4 is
   begin
      return
        (1 => Cell (Rule, 0, Input (1), Input (2)),
         2 => Cell (Rule, Input (1), Input (2), Input (3)),
         3 => Cell (Rule, Input (2), Input (3), Input (4)),
         4 => Cell (Rule, Input (3), Input (4), 0));
   end Step4;
end Automata_Reference;
