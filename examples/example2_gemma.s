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
	add	x1, sp, #8
	bl	_ZNSirsERi
	mov	x0, x19
	add	x1, sp, #4
	bl	_ZStrsIcSt11char_traitsIcEERSt13basic_istreamIT_T0_ES6_RS3_
	ldrb	w20, [sp, #4]
	cmp	w20, #48
	beq	.L_done
	ldr	w21, [sp, #8]
	mov	w22, #1
.L_loop:
	cmp	w21, #1
	ble	.L_done
	mov	x0, x19
	add	x1, sp, #4
	bl	_ZStrsIcSt11char_traitsIcEERSt13basic_istreamIT_T0_ES6_RS3_
	add	w22, w22, #1
	sub	w21, w21, #1
	ldrb	w20, [sp, #4]
	cmp	w20, #48
	bne	.L_loop
.L_done:
	mov	w1, w22
	adrp	x0, _ZSt4cout
	add	x0, x0, :lo12:_ZSt4cout
	bl	_ZNSolsEi
	mov	w0, #0
	add	sp, sp, #16
	ldp	x29, x30, [sp], #32
	ret