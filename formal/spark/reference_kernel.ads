-- SPARK-REFERENCE-KERNEL/1 — finite, explicit, pure reference semantics.
-- A contract is a proof OBLIGATION, not a discharged proof by itself.
package Reference_Kernel with SPARK_Mode => On is
   subtype Width_Type is Positive range 1 .. 16;
   subtype Coordinate is Natural range 0 .. 15;
   subtype Cell_Index is Natural range 0 .. 255;
   subtype Node_Count is Positive range 2 .. 256;
   type Bit is mod 2;
   type Phase is mod 3;

   function Address (Row, Column : Coordinate; Width : Width_Type)
      return Cell_Index
   with
      Pre => Column < Width,
      Post => Natural (Address'Result) =
         Natural (Row) * Natural (Width) + Natural (Column);

   function Decode_Row (Position : Cell_Index; Width : Width_Type)
      return Coordinate
   with
      Pre => Natural (Position) < Natural (Width) * 16,
      Post => Natural (Decode_Row'Result) =
         Natural (Position) / Natural (Width);

   function Decode_Column (Position : Cell_Index; Width : Width_Type)
      return Coordinate
   with
      Pre => Natural (Position) < Natural (Width) * 16,
      Post => Natural (Decode_Column'Result) =
         Natural (Position) mod Natural (Width);

   function Parity_Add (Left, Right : Bit) return Bit
   with Post => Parity_Add'Result = (Left xor Right);

   function Parity_Mul (Left, Right : Bit) return Bit
   with Post => Parity_Mul'Result = (Left and Right);

   function Phase_Add (Left, Right : Phase) return Phase
   with Post => Phase_Add'Result = Left + Right;

   function Valid_Edge (Source, Target : Cell_Index; Count : Node_Count)
      return Boolean
   with Post => Valid_Edge'Result =
      (Source < Count and Target < Count and Source /= Target);

   function Edge_Step
      (Source, Target : Cell_Index; Count : Node_Count;
       Current, Influence : Bit) return Bit
   with
      Pre => Valid_Edge (Source, Target, Count),
      Post => Edge_Step'Result = Parity_Add (Current, Influence);
end Reference_Kernel;
