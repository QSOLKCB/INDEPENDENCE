-- The lexical input/output boundary is not SPARK-proved; it is differential-tested.
with Ada.Command_Line;
with Ada.Text_IO;
with Automaton_Kernel;
procedure Automaton_CLI is
   package CLI renames Ada.Command_Line;
   package K renames Automaton_Kernel;
   function Decimal (Index : Positive) return Natural is
      Text : constant String := CLI.Argument (Index);
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
begin
   if CLI.Argument_Count /= 4 then
      Ada.Text_IO.Put_Line ("ERR:INVALID");
      return;
   end if;
   declare
      Rule : constant Natural := Decimal (1);
      Left : constant Natural := Decimal (2);
      Center : constant Natural := Decimal (3);
      Right : constant Natural := Decimal (4);
   begin
      if Rule > 255 or Left > 1 or Center > 1 or Right > 1 then
         Ada.Text_IO.Put_Line ("ERR:INVALID");
      else
         if K.Next_Bit (K.Rule_Type (Rule), K.Bit (Left),
                        K.Bit (Center), K.Bit (Right)) = 1 then
            Ada.Text_IO.Put_Line ("OK:1");
         else
            Ada.Text_IO.Put_Line ("OK:0");
         end if;
      end if;
   end;
exception
   when Constraint_Error =>
      Ada.Text_IO.Put_Line ("ERR:INVALID");
end Automaton_CLI;
