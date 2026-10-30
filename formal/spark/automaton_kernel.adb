package body Automaton_Kernel with SPARK_Mode => On is
   function Next_Bit (Rule : Rule_Type; Left, Center, Right : Bit)
      return Bit is
      Index : constant Natural :=
        4 * Natural (Left) + 2 * Natural (Center) + Natural (Right);
   begin
      return Bit ((Natural (Rule) / (2 ** Index)) mod 2);
   end Next_Bit;
end Automaton_Kernel;
