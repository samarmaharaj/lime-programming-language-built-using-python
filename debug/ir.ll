; ModuleID = "main"
target triple = "x86_64-pc-windows-msvc"
target datalayout = ""

declare i32 @"printf"(i8* %".1", ...)

@"true" = internal constant i1 1
@"false" = internal constant i1 0
define i32 @"main"()
{
main_entry:
  %".2" = alloca i32
  store i32 5, i32* %".2"
  %".4" = alloca i32
  store i32 10, i32* %".4"
  %".6" = load i32, i32* %".2"
  %".7" = load i32, i32* %".4"
  %".8" = add i32 %".6", %".7"
  %".9" = alloca [13 x i8]*
  store [13 x i8]* @"__str_1", [13 x i8]** %".9"
  %".11" = bitcast [13 x i8]* @"__str_1" to i8*
  %".12" = call i32 (i8*, ...) @"printf"(i8* %".11", i32 %".8")
  %".13" = load i32, i32* %".2"
  %".14" = load i32, i32* %".4"
  %".15" = add i32 %".13", %".14"
  ret i32 %".15"
}

@"__str_1" = internal constant [13 x i8] c"a + b = %i\0a\00\00"