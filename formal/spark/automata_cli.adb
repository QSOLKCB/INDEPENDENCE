-- Development-only CLI, deliberately outside the SPARK proof boundary.
with Ada.Command_Line;
with Ada.Text_IO;
with Automata_Reference;
procedure Automata_CLI is
   package Arguments renames Ada.Command_Line;
   package IO renames Ada.Text_IO;
   package K renames Automata_Reference;

   function Decimal (Position : Positive) return Natural is
      Text : constant String := Arguments.Argument (Position);
   begin
      if Text'Length = 0 then
         raise Constraint_Error;
      end if;
      for C of Text loop
         if C not in '0' .. '9' then
            raise Constraint_Error;
         end if;
      end loop;
      return Natural'Value (Text);
   end Decimal;

   function Digit (Value : K.Bit) return Character is
   begin
      if Value = 0 then
         return '0';
      else
         return '1';
      end if;
   end Digit;
begin
   if Arguments.Argument_Count /= 5 then
      IO.Put_Line ("ERR:INVALID");
      return;
   end if;
   declare
      Rule : constant K.Rule_Byte := K.Rule_Byte (Decimal (1));
      Input : constant K.Row4 :=
        (1 => K.Bit (Decimal (2)), 2 => K.Bit (Decimal (3)),
         3 => K.Bit (Decimal (4)), 4 => K.Bit (Decimal (5)));
      Output : constant K.Row4 := K.Step4 (Rule, Input);
   begin
      IO.Put_Line ("OK:" & Digit (Output (1)) & Digit (Output (2)) &
                   Digit (Output (3)) & Digit (Output (4)));
   exception
      when Constraint_Error => IO.Put_Line ("ERR:INVALID");
   end;
end Automata_CLI;
