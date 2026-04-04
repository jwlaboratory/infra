.arch armv8-a
	.file	"submission.cpp"
	.text
	.section	.text._ZnwmPv,"axG",@progbits,_ZnwmPv,comdat
	.align	2
	.weak	_ZnwmPv
	.type	_ZnwmPv, %function
_ZnwmPv:
.LFB469:
	.cfi_startproc
	sub	sp, sp, #16
	.cfi_def_cfa_offset 16
	str	x0, [sp, 8]
	str	x1, [sp]
	ldr	x0, [sp]
	add	sp, sp, 16
	.cfi_def_cfa_offset 0
	ret
	.cfi_endproc
.LFE469:
	.size	_ZnwmPv, .-_ZnwmPv
	.section	.text._ZdlPvS_,"axG",@progbits,_ZdlPvS_,comdat
	.align	2
	.weak	_ZdlPvS_
	.type	_ZdlPvS_, %function
_ZdlPvS_:
.LFB471:
	.cfi_startproc
	sub	sp, sp, #16
	.cfi_def_cfa_offset 16
	str	x0, [sp, 8]
	str	x1, [sp]
	nop
	add	sp, sp, 16
	.cfi_def_cfa_offset 0
	ret
	.cfi_endproc
.LFE471:
	.size	_ZdlPvS_, .-_ZdlPvS_
	.global	n
	.bss
	.align	2
	.type	n, %object
	.size	n, 4
n:
	.zero	4
	.global	m
	.align	2
	.type	m, %object
	.size	m, 4
m:
	.zero	4
	.global	k
	.align	2
	.type	k, %object
	.size	k, 4
k:
	.zero	4
	.global	g
	.bss
	.align	3
	.type	g, %object
	.size	g, 9600240
g:
	.zero	9600240
	.global	winLine
	.align	3
	.type	winLine, %object
	.size	winLine, 800020
winLine:
	.zero	800020
	.section	.rodata
	.align	3
.LC0:
	.string	"Bhinneka"
	.align	3
.LC1:
	.string	"Chaneka"
	.text
	.align	2
	.global	main
	.type	main, %function
main:
.LFB9779:
	.cfi_startproc
	stp	x29, x30, [sp, -144]!
	.cfi_def_cfa_offset 144
	.cfi_offset 29, -144
	.cfi_offset 30, -136
	mov	x29, sp
	str	x19, [sp, 16]
	.cfi_offset 19, -128
	mov	w0, 0
	bl	_ZNSt8ios_base15sync_with_stdioEb
	mov	x1, 0
	adrp	x0, _ZSt3cin+16
	add	x0, x0, :lo12:_ZSt3cin+16
	bl	_ZNSt9basic_iosIcSt11char_traitsIcEE3tieEPSo
	mov	x1, 0
	adrp	x0, _ZSt4cout+8
	add	x0, x0, :lo12:_ZSt4cout+8
	bl	_ZNSt9basic_iosIcSt11char_traitsIcEE3tieEPSo
	adrp	x0, n
	add	x1, x0, :lo12:n
	adrp	x0, _ZSt3cin
	add	x0, x0, :lo12:_ZSt3cin
	bl	_ZNSirsERi
	mov	x2, x0
	adrp	x0, m
	add	x1, x0, :lo12:m
	mov	x0, x2
	bl	_ZNSirsERi
	mov	x2, x0
	adrp	x0, k
	add	x1, x0, :lo12:k
	mov	x0, x2
	bl	_ZNSirsERi
	adrp	x0, n
	add	x0, x0, :lo12:n
	ldr	w0, [x0]
	cmp	w0, 1
	bne	.L11
	adrp	x0, m
	add	x0, x0, :lo12:m
	ldr	w0, [x0]
	cmp	w0, 1
	bne	.L11
	adrp	x0, k
	add	x0, x0, :lo12:k
	ldr	w0, [x0]
	cmp	w0, 0
	bne	.L11
	adrp	x0, .LC0
	add	x1, x0, :lo12:.LC0
	adrp	x0, _ZSt4cout
	add	x0, x0, :lo12:_ZSt4cout
	bl	_ZStlsISt11char_traitsIcEERSt13basic_ostreamIcT_ES5_PKc
	mov	w0, 0
	b	.L36
.L11:
	adrp	x0, n
	add	x0, x0, :lo12:n
	ldr	w0, [x0]
	cmp	w0, 1
	beq	.L13
	adrp	x0, m
	add	x0, x0, :lo12:m
	ldr	w0, [x0]
	cmp	w0, 1
	bne	.L14
.L13:
	adrp	x0, .LC1
	add	x1, x0, :lo12:.LC1
	adrp	x0, _ZSt4cout
	add	x0, x0, :lo12:_ZSt4cout
	bl	_ZStlsISt11char_traitsIcEERSt13basic_ostreamIcT_ES5_PKc
	mov	w0, 0
	b	.L36
.L14:
	mov	w0, 1
	str	w0, [sp, 140]
	b	.L15
.L18:
	add	x0, sp, 72
	mov	x1, x0
	adrp	x0, _ZSt3cin
	add	x0, x0, :lo12:_ZSt3cin
	bl	_ZNSirsERi
	mov	x2, x0
	add	x0, sp, 68
	mov	x1, x0
	mov	x0, x2
	bl	_ZNSirsERi
	ldr	w0, [sp, 72]
	sxtw	x1, w0
	mov	x0, x1
	lsl	x0, x0, 1
	add	x0, x0, x1
	lsl	x0, x0, 4
	adrp	x1, g
	add	x1, x1, :lo12:g
	add	x0, x0, x1
	add	x1, sp, 68
	bl	_ZNSt3setIiSt4lessIiESaIiEE6insertERKi
	ldr	w0, [sp, 72]
	cmp	w0, 1
	beq	.L16
	ldr	w0, [sp, 68]
	cmp	w0, 1
	bne	.L17
.L16:
	adrp	x0, .LC1
	add	x1, x0, :lo12:.LC1
	adrp	x0, _ZSt4cout
	add	x0, x0, :lo12:_ZSt4cout
	bl	_ZStlsISt11char_traitsIcEERSt13basic_ostreamIcT_ES5_PKc
	mov	w0, 0
	b	.L36
.L17:
	ldr	w0, [sp, 140]
	add	w0, w0, 1
	str	w0, [sp, 140]
.L15:
	adrp	x0, k
	add	x0, x0, :lo12:k
	ldr	w0, [x0]
	ldr	w1, [sp, 140]
	cmp	w1, w0
	ble	.L18
	adrp	x0, m
	add	x0, x0, :lo12:m
	ldr	w0, [x0]
	str	w0, [sp, 76]
	adrp	x0, n
	add	x0, x0, :lo12:n
	ldr	w0, [x0]
	str	w0, [sp, 136]
	b	.L19
.L33:
	ldr	w0, [sp, 76]
	cmp	w0, 0
	beq	.L37
	ldrsw	x1, [sp, 136]
	mov	x0, x1
	lsl	x0, x0, 1
	add	x0, x0, x1
	lsl	x0, x0, 4
	adrp	x1, g
	add	x1, x1, :lo12:g
	add	x0, x0, x1
	bl	_ZNKSt3setIiSt4lessIiESaIiEE5emptyEv
	and	w0, w0, 255
	and	w0, w0, 1
	cmp	w0, 0
	bne	.L22
	ldrsw	x1, [sp, 136]
	mov	x0, x1
	lsl	x0, x0, 1
	add	x0, x0, x1
	lsl	x0, x0, 4
	adrp	x1, g
	add	x1, x1, :lo12:g
	add	x0, x0, x1
	bl	_ZNKSt3setIiSt4lessIiESaIiEE3endEv
	str	x0, [sp, 56]
	mov	x0, 1
	str	x0, [sp, 112]
	ldr	x0, [sp, 112]
	neg	x0, x0
	str	x0, [sp, 104]
	ldr	x0, [sp, 104]
	str	x0, [sp, 96]
	add	x0, sp, 56
	str	x0, [sp, 88]
	nop
	add	x0, sp, 56
	mov	w2, w19
	ldr	x1, [sp, 96]
	bl	_ZSt9__advanceISt23_Rb_tree_const_iteratorIiElEvRT_T0_St26bidirectional_iterator_tag
	nop
	ldr	x0, [sp, 56]
	str	x0, [sp, 80]
	add	x0, sp, 80
	bl	_ZNKSt23_Rb_tree_const_iteratorIiEdeEv
	ldr	w1, [x0]
	ldr	w0, [sp, 76]
	cmp	w1, w0
	bge	.L25
.L22:
	mov	w0, 1
	b	.L26
.L25:
	mov	w0, 0
.L26:
	and	w0, w0, 1
	cmp	w0, 0
	beq	.L27
	ldrsw	x1, [sp, 136]
	mov	x0, x1
	lsl	x0, x0, 1
	add	x0, x0, x1
	lsl	x0, x0, 4
	adrp	x1, g
	add	x1, x1, :lo12:g
	add	x0, x0, x1
	add	x1, sp, 76
	bl	_ZNSt3setIiSt4lessIiESaIiEE6insertERKi
	ldr	w0, [sp, 76]
	sub	w0, w0, #1
	str	w0, [sp, 76]
.L27:
	ldrsw	x1, [sp, 136]
	mov	x0, x1
	lsl	x0, x0, 1
	add	x0, x0, x1
	lsl	x0, x0, 4
	adrp	x1, g
	add	x1, x1, :lo12:g
	add	x0, x0, x1
	str	x0, [sp, 128]
	ldr	x0, [sp, 128]
	bl	_ZNKSt3setIiSt4lessIiESaIiEE5beginEv
	str	x0, [sp, 48]
	ldr	x0, [sp, 128]
	bl	_ZNKSt3setIiSt4lessIiESaIiEE3endEv
	str	x0, [sp, 40]
	b	.L28
.L29:
	add	x0, sp, 48
	bl	_ZNKSt23_Rb_tree_const_iteratorIiEdeEv
	ldr	w0, [x0]
	str	w0, [sp, 124]
	adrp	x0, winLine
	add	x0, x0, :lo12:winLine
	ldrsw	x1, [sp, 124]
	mov	w2, 1
	str	w2, [x0, x1, lsl 2]
	add	x0, sp, 48
	bl	_ZNSt23_Rb_tree_const_iteratorIiEppEv
.L28:
	add	x1, sp, 40
	add	x0, sp, 48
	bl	_ZStneRKSt23_Rb_tree_const_iteratorIiES2_
	and	w0, w0, 255
	and	w0, w0, 1
	cmp	w0, 0
	bne	.L29
	b	.L30
.L32:
	ldr	w0, [sp, 76]
	sub	w0, w0, #1
	str	w0, [sp, 76]
.L30:
	ldr	w0, [sp, 76]
	cmp	w0, 0
	ble	.L31
	ldr	w1, [sp, 76]
	adrp	x0, winLine
	add	x0, x0, :lo12:winLine
	sxtw	x1, w1
	ldr	w0, [x0, x1, lsl 2]
	cmp	w0, 0
	bne	.L32
.L31:
	ldr	w0, [sp, 136]
	sub	w0, w0, #1
	str	w0, [sp, 136]
.L19:
	ldr	w0, [sp, 136]
	cmp	w0, 1
	bgt	.L33
	b	.L21
.L37:
	nop
.L21:
	ldr	w0, [sp, 76]
	cmp	w0, 1
	bne	.L34
	adrp	x0, .LC0
	add	x1, x0, :lo12:.LC0
	adrp	x0, _ZSt4cout
	add	x0, x0, :lo12:_ZSt4cout
	bl	_ZStlsISt11char_traitsIcEERSt13basic_ostreamIcT_ES5_PKc
	b	.L35
.L34:
	adrp	x0, .LC1
	add	x1, x0, :lo12:.LC1
	adrp	x0, _ZSt4cout
	add	x0, x0, :lo12:_ZSt4cout
	bl	_ZStlsISt11char_traitsIcEERSt13basic_ostreamIcT_ES5_PKc
.L35:
	mov	w0, 0
.L36:
	ldr	x19, [sp, 16]
	ldp	x29, x30, [sp], 144
	.cfi_restore 30
	.cfi_restore 29
	.cfi_restore 19
	.cfi_def_cfa_offset 0
	ret
	.cfi_endproc
.LFE9779:
	.size	main, .-main
	.ident	"GCC: (GNU) 13.4.0"
	.section	.note.GNU-stack,"",@progbits

