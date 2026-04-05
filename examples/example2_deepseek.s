.arch armv8-a
.file "submission_0018.cpp"
.text
#APP
.globl _ZSt21ios_base_library_initv
#NO_APP
.section .text.startup,"ax",@progbits
.align 2
.p2align 4,,11
.global main
.type main, %function
main:
.LFB2007:
.cfi_startproc
stp x29, x30, [sp, -48]!
.cfi_def_cfa_offset 48
.cfi_offset 29, -48
.cfi_offset 30, -40
mov x29, sp
stp x19, x20, [sp, 16]
.cfi_offset 19, -32
.cfi_offset 20, -24
adrp x20, _ZSt3cin
add x20, x20, :lo12:_ZSt3cin
add x1, sp, 44
mov x0, x20
bl _ZNSirsERi
add x1, sp, 43
mov x0, x20
bl _ZStrsIcSt11char_traitsIcEERSt13basic_istreamIT_T0_ES6_RS3_
ldr w2, [sp, 44]
ldrb w0, [sp, 43]
mov w19, 1
cmp w0, 48
beq .L2
cmp w2, 1
ble .L2
.p2align 2,,3
.L3:
add x1, sp, 43
mov x0, x20
bl _ZStrsIcSt11char_traitsIcEERSt13basic_istreamIT_T0_ES6_RS3_
add w19, w19, 1
sub w2, w2, 1
str w2, [sp, 44]
ldrb w0, [sp, 43]
cmp w0, 48
beq .L2
cmp w2, 1
bgt .L3
.L2:
mov w1, w19
adrp x0, _ZSt4cout
add x0, x0, :lo12:_ZSt4cout
bl _ZNSolsEi
mov w0, 0
ldp x19, x20, [sp, 16]
ldp x29, x30, [sp], 48
.cfi_def_cfa_offset 0
ret
.cfi_endproc
.LFE2007:
.size main, .-main
.ident "GCC: (GNU) 13.4.0"
.section .note.GNU-stack,"",@progbits