-- CLI is deliberately OUTSIDE SPARK: external input and I/O are not proved.
with Ada.Command_Line;
with Ada.Text_IO;
with Ada.Strings;
with Ada.Strings.Fixed;
with Reference_Kernel;
procedure Reference_CLI is
   package CLI renames Ada.Command_Line;
   package IO renames Ada.Text_IO;
   package K renames Reference_Kernel;

   function Img (Value : Natural) return String is
   begin
      return Ada.Strings.Fixed.Trim (Natural'Image (Value), Ada.Strings.Both);
   end Img;

   function N (Index : Positive) return Natural is
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
   end N;

begin
   if CLI.Argument_Count < 1 then
      IO.Put_Line ("ERR:INVALID");
      return;
   end if;
   declare
      Op : constant String := CLI.Argument (1);
   begin
      if Op = "ADDR" and CLI.Argument_Count = 4 then
         declare
            R : constant K.Coordinate := K.Coordinate (N (2));
            C : constant K.Coordinate := K.Coordinate (N (3));
            W : constant K.Width_Type := K.Width_Type (N (4));
         begin
            if C >= W then
               IO.Put_Line ("ERR:INVALID");
            else
               IO.Put_Line ("OK:" & Img (K.Address (R, C, W)));
            end if;
         end;
      elsif Op = "DECODE" and CLI.Argument_Count = 3 then
         declare
            Pos : constant K.Cell_Index := K.Cell_Index (N (2));
            W : constant K.Width_Type := K.Width_Type (N (3));
         begin
            if Natural (Pos) >= Natural (W) * 16 then
               IO.Put_Line ("ERR:INVALID");
            else
               IO.Put_Line ("OK:" & Img (K.Decode_Row (Pos, W)) & "," &
                            Img (K.Decode_Column (Pos, W)));
            end if;
         end;
      elsif Op = "PARITY_ADD" and CLI.Argument_Count = 3 then
         if N (2) > 1 or N (3) > 1 then
            IO.Put_Line ("ERR:INVALID");
         else
            IO.Put_Line ("OK:" & Img (Natural (K.Parity_Add
              (K.Bit (N (2)), K.Bit (N (3))))));
         end if;
      elsif Op = "PARITY_MUL" and CLI.Argument_Count = 3 then
         if N (2) > 1 or N (3) > 1 then
            IO.Put_Line ("ERR:INVALID");
         else
            IO.Put_Line ("OK:" & Img (Natural (K.Parity_Mul
              (K.Bit (N (2)), K.Bit (N (3))))));
         end if;
      elsif Op = "PHASE_ADD" and CLI.Argument_Count = 3 then
         if N (2) > 2 or N (3) > 2 then
            IO.Put_Line ("ERR:INVALID");
         else
            IO.Put_Line ("OK:" & Img (Natural (K.Phase_Add
              (K.Phase (N (2)), K.Phase (N (3))))));
         end if;
      elsif Op = "EDGE_VALID" and CLI.Argument_Count = 4 then
         declare
            Valid : constant Boolean := K.Valid_Edge
              (K.Cell_Index (N (2)), K.Cell_Index (N (3)),
               K.Node_Count (N (4)));
         begin
            IO.Put_Line (if Valid then "OK:1" else "OK:0");
         end;
      elsif Op = "EDGE_STEP" and CLI.Argument_Count = 6 then
         declare
            Source : constant K.Cell_Index := K.Cell_Index (N (2));
            Target : constant K.Cell_Index := K.Cell_Index (N (3));
            Count : constant K.Node_Count := K.Node_Count (N (4));
         begin
            if not K.Valid_Edge (Source, Target, Count) or
               N (5) > 1 or N (6) > 1 then
               IO.Put_Line ("ERR:INVALID");
            else
               IO.Put_Line ("OK:" & Img (Natural (K.Edge_Step
                 (Source, Target, Count, K.Bit (N (5)), K.Bit (N (6))))));
            end if;
         end;
      else
         IO.Put_Line ("ERR:INVALID");
      end if;
   exception
      when Constraint_Error => IO.Put_Line ("ERR:INVALID");
   end;
end Reference_CLI;
