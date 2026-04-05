	.arch armv8-a
	.text
	.align 2
	.global main
	.type main, %function
main:
	stp	x29, x30, [sp, -32]!
	mov	x29, sp
	adrp	x19, _ZSt3cin
	add	x19, x19, :lo12:_ZSt3cin
	sub	sp, sp, #16
	mov	x0, x19
	mov	x1, sp
	bl	_ZNSirsERi
	mov	x0, x19
	mov	x1, sp
	add	x1, x1, #4
	bl	_ZStrsIcSt11char_traitsIcEERSt13basic_istreamIT_T0_ES6_RS3_
	ldr	w20, [sp]
	ldrb	w21, [sp, #4]
	mov	w22, #1
	cmp	w21, #48
	beq	.L_exit
	cmp	w20, #1
	ble	.L_exit
.L_loop:
	mov	x0, x19
	mov	x1, sp
	add	x1, x1, #4
	bl	_ZStrsIcSt11char_traitsIcEERSt13basic_istreamIT_T0_ES6_RS3_
	add	w22, w22, #1
	ldr	w20, [sp]
	sub	w20, w20, #1
	str	w20, [sp]
	ldrb	w21, [sp, #4]
	cmp	w21, #48
	beq	.L_exit
	cmp	w20, #1
	bgt	.L_loop
.L_exit:
	mov	w1, w22
	adrp	x0, _ZSt4cout
	add	x0, x0, :lo12:_ZSt4cout
	bl	_ZNSolsEi
	mov	w0, #0
	add	sp, sp, #16
	ldp	x29, x30, [sp], #32
	ret