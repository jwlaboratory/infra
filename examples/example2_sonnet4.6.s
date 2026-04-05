.arch armv8-a
	.file	"submission_0018.cpp"
	.text
#APP
	.globl _ZSt21ios_base_library_initv
#NO_APP
	.section	.text.startup,"ax",@progbits
	.align	2
	.p2align 4,,11
	.global	main
	.type	main, %function
main:
	.cfi_startproc
	stp	x29, x30, [sp, -48]!
	.cfi_def_cfa_offset 48
	.cfi_offset 29, -48
	.cfi_offset 30, -40
	mov	x29, sp
	stp	x19, x20, [sp, 16]
	.cfi_offset 19, -32
	.cfi_offset 20, -24
	adrp	x20, _ZSt3cin
	add	x20, x20, :lo12:_ZSt3cin
	add	x1, sp, 44
	mov	x0, x20
	bl	_ZNSirsERi
	ldr	w19, [sp, 44]
	cmp	w19, 1
	ble	.L_res1
	add	x1, sp, 43
	mov	x0, x20
	bl	_ZStrsIcSt11char_traitsIcEERSt13basic_istreamIT_T0_ES6_RS3_
	ldrb	w2, [sp, 43]
	cmp	w2, 48
	beq	.L_res1
	mov	w0, 1
.L_loop:
	add	x1, sp, 43
	mov	x0, x20
	add	w0, w0, 1
	sub	w19, w19, 1
	bl	_ZStrsIcSt11char_traitsIcEERSt13basic_istreamIT_T0_ES6_RS3_
	ldrb	w2, [sp, 43]
	cmp	w2, 48
	beq	.L_done
	cmp	w19, 1
	bgt	.L_loop
	b	.L_done
.L_res1:
	mov	w0, 1
.L_done:
	mov	w1, w0
	adrp	x0, _ZSt4cout
	add	x0, x0, :lo12:_ZSt4cout
	bl	_ZNSolsEi
	ldp	x19, x20, [sp, 16]
	mov	w0, 0
	ldp	x29, x30, [sp], 48
	.cfi_restore 30
	.cfi_restore 29
	.cfi_restore 19
	.cfi_restore 20
	.cfi_def_cfa_offset 0
	ret
	.cfi_endproc
	.size	main, .-main
	.ident	"GCC: (GNU) 13.4.0"
	.section	.note.GNU-stack,"",@progbits