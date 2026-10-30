package body Reference_Kernel with SPARK_Mode => On is
   function Address (Row, Column : Coordinate; Width : Width_Type)
      return Cell_Index is
   begin
      return Cell_Index (Natural (Row) * Natural (Width) + Natural (Column));
   end Address;

   function Decode_Row (Position : Cell_Index; Width : Width_Type)
      return Coordinate is
   begin
      return Coordinate (Natural (Position) / Natural (Width));
   end Decode_Row;

   function Decode_Column (Position : Cell_Index; Width : Width_Type)
      return Coordinate is
   begin
      return Coordinate (Natural (Position) mod Natural (Width));
   end Decode_Column;

   function Parity_Add (Left, Right : Bit) return Bit is
   begin
      return Left xor Right;
   end Parity_Add;

   function Parity_Mul (Left, Right : Bit) return Bit is
   begin
      return Left and Right;
   end Parity_Mul;

   function Phase_Add (Left, Right : Phase) return Phase is
   begin
      return Left + Right;
   end Phase_Add;

   function Valid_Edge (Source, Target : Cell_Index; Count : Node_Count)
      return Boolean is
   begin
      return Source < Count and Target < Count and Source /= Target;
   end Valid_Edge;

   function Edge_Step
      (Source, Target : Cell_Index; Count : Node_Count;
       Current, Influence : Bit) return Bit is
   begin
      return Parity_Add (Current, Influence);
   end Edge_Step;
end Reference_Kernel;
