; ModuleID = "main"
target triple = "x86_64-pc-windows-msvc"
target datalayout = ""

define i32 @"main"()
{
main_entry:
  %".2" = fmul float 0x4010ccccc0000000, 0x4008000000000000
  ret i32 69
}
