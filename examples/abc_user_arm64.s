	.arch armv8-a
	.file	"abc_ref.cpp"
	.text
#APP
	.globl _ZSt21ios_base_library_initv
#NO_APP
	.align	2
	.p2align 4,,11
	.type	_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE8_M_eraseEPSt13_Rb_tree_nodeIiE.isra.0, %function
_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE8_M_eraseEPSt13_Rb_tree_nodeIiE.isra.0:
.LFB11676:
	.cfi_startproc
	cbz	x0, .L63
	stp	x29, x30, [sp, -96]!
	.cfi_def_cfa_offset 96
	.cfi_offset 29, -96
	.cfi_offset 30, -88
	mov	x29, sp
	stp	x23, x24, [sp, 48]
	.cfi_offset 23, -48
	.cfi_offset 24, -40
	mov	x23, x0
	stp	x19, x20, [sp, 16]
	.cfi_offset 19, -80
	.cfi_offset 20, -72
.L19:
	ldr	x24, [x23, 24]
	cbz	x24, .L3
	stp	x25, x26, [sp, 64]
	.cfi_offset 26, -24
	.cfi_offset 25, -32
.L18:
	ldr	x25, [x24, 24]
	cbz	x25, .L4
.L17:
	ldr	x26, [x25, 24]
	cbz	x26, .L5
.L16:
	ldr	x19, [x26, 24]
	cbz	x19, .L6
.L15:
	ldr	x20, [x19, 24]
	cbz	x20, .L7
	stp	x21, x22, [sp, 32]
	.cfi_offset 22, -56
	.cfi_offset 21, -64
	str	x27, [sp, 80]
	.cfi_offset 27, -16
.L14:
	ldr	x27, [x20, 24]
	cbz	x27, .L8
.L13:
	ldr	x21, [x27, 24]
	cbz	x21, .L9
.L12:
	ldr	x22, [x21, 24]
	cbz	x22, .L10
.L11:
	ldr	x0, [x22, 24]
	bl	_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE8_M_eraseEPSt13_Rb_tree_nodeIiE.isra.0
	mov	x0, x22
	mov	x1, 40
	ldr	x22, [x22, 16]
	bl	_ZdlPvm
	cbnz	x22, .L11
.L10:
	ldr	x22, [x21, 16]
	mov	x0, x21
	mov	x1, 40
	bl	_ZdlPvm
	cbz	x22, .L9
	mov	x21, x22
	b	.L12
.L64:
	ldp	x21, x22, [sp, 32]
	.cfi_restore 22
	.cfi_restore 21
	ldr	x27, [sp, 80]
	.cfi_restore 27
.L7:
	mov	x0, x19
	ldr	x20, [x19, 16]
	mov	x1, 40
	bl	_ZdlPvm
	cbz	x20, .L6
	mov	x19, x20
	b	.L15
	.p2align 2,,3
.L8:
	.cfi_offset 21, -64
	.cfi_offset 22, -56
	.cfi_offset 27, -16
	ldr	x21, [x20, 16]
	mov	x0, x20
	mov	x1, 40
	bl	_ZdlPvm
	cbz	x21, .L64
	mov	x20, x21
	b	.L14
.L6:
	.cfi_restore 21
	.cfi_restore 22
	.cfi_restore 27
	ldr	x19, [x26, 16]
	mov	x0, x26
	mov	x1, 40
	bl	_ZdlPvm
	cbz	x19, .L5
	mov	x26, x19
	b	.L16
	.p2align 2,,3
.L9:
	.cfi_offset 21, -64
	.cfi_offset 22, -56
	.cfi_offset 27, -16
	ldr	x21, [x27, 16]
	mov	x0, x27
	mov	x1, 40
	bl	_ZdlPvm
	cbz	x21, .L8
	mov	x27, x21
	b	.L13
.L5:
	.cfi_restore 21
	.cfi_restore 22
	.cfi_restore 27
	ldr	x19, [x25, 16]
	mov	x0, x25
	mov	x1, 40
	bl	_ZdlPvm
	cbz	x19, .L4
	mov	x25, x19
	b	.L17
.L4:
	ldr	x19, [x24, 16]
	mov	x0, x24
	mov	x1, 40
	bl	_ZdlPvm
	cbz	x19, .L65
	mov	x24, x19
	b	.L18
.L65:
	ldp	x25, x26, [sp, 64]
	.cfi_restore 26
	.cfi_restore 25
.L3:
	mov	x0, x23
	ldr	x19, [x23, 16]
	mov	x1, 40
	bl	_ZdlPvm
	cbz	x19, .L66
	mov	x23, x19
	b	.L19
.L66:
	ldp	x19, x20, [sp, 16]
	ldp	x23, x24, [sp, 48]
	ldp	x29, x30, [sp], 96
	.cfi_restore 30
	.cfi_restore 29
	.cfi_restore 23
	.cfi_restore 24
	.cfi_restore 19
	.cfi_restore 20
	.cfi_def_cfa_offset 0
	ret
.L63:
	ret
	.cfi_endproc
.LFE11676:
	.size	_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE8_M_eraseEPSt13_Rb_tree_nodeIiE.isra.0, .-_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE8_M_eraseEPSt13_Rb_tree_nodeIiE.isra.0
	.align	2
	.p2align 4,,11
	.type	__tcf_0, %function
__tcf_0:
.LFB11651:
	.cfi_startproc
	stp	x29, x30, [sp, -48]!
	.cfi_def_cfa_offset 48
	.cfi_offset 29, -48
	.cfi_offset 30, -40
	mov	x29, sp
	stp	x19, x20, [sp, 16]
	.cfi_offset 19, -32
	.cfi_offset 20, -24
	adrp	x20, g+9600192
	add	x20, x20, :lo12:g+9600192
	str	x21, [sp, 32]
	.cfi_offset 21, -16
	adrp	x21, g
	add	x21, x21, :lo12:g
	.p2align 3,,7
.L70:
	ldr	x19, [x20, 16]
	cbz	x19, .L68
.L69:
	ldr	x0, [x19, 24]
	bl	_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE8_M_eraseEPSt13_Rb_tree_nodeIiE.isra.0
	mov	x0, x19
	mov	x1, 40
	ldr	x19, [x19, 16]
	bl	_ZdlPvm
	cbnz	x19, .L69
.L68:
	sub	x0, x20, #48
	cmp	x21, x20
	beq	.L77
	mov	x20, x0
	b	.L70
.L77:
	ldp	x19, x20, [sp, 16]
	ldr	x21, [sp, 32]
	ldp	x29, x30, [sp], 48
	.cfi_restore 30
	.cfi_restore 29
	.cfi_restore 21
	.cfi_restore 19
	.cfi_restore 20
	.cfi_def_cfa_offset 0
	ret
	.cfi_endproc
.LFE11651:
	.size	__tcf_0, .-__tcf_0
	.section	.text._ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE16_M_insert_uniqueIRKiEESt4pairISt17_Rb_tree_iteratorIiEbEOT_,"axG",@progbits,_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE16_M_insert_uniqueIRKiEESt4pairISt17_Rb_tree_iteratorIiEbEOT_,comdat
	.align	2
	.p2align 4,,11
	.weak	_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE16_M_insert_uniqueIRKiEESt4pairISt17_Rb_tree_iteratorIiEbEOT_
	.type	_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE16_M_insert_uniqueIRKiEESt4pairISt17_Rb_tree_iteratorIiEbEOT_, %function
_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE16_M_insert_uniqueIRKiEESt4pairISt17_Rb_tree_iteratorIiEbEOT_:
.LFB10960:
	.cfi_startproc
	stp	x29, x30, [sp, -80]!
	.cfi_def_cfa_offset 80
	.cfi_offset 29, -80
	.cfi_offset 30, -72
	mov	x29, sp
	stp	x19, x20, [sp, 16]
	.cfi_offset 19, -64
	.cfi_offset 20, -56
	ldr	w20, [x1]
	ldr	x19, [x0, 16]
	stp	x21, x22, [sp, 32]
	.cfi_offset 21, -48
	.cfi_offset 22, -40
	mov	x21, x0
	stp	x23, x24, [sp, 48]
	mov	x22, x1
	.cfi_offset 23, -32
	.cfi_offset 24, -24
	add	x24, x0, 8
	str	x25, [sp, 64]
	.cfi_offset 25, -16
	cbz	x19, .L79
	mov	w6, 1
	b	.L81
	.p2align 2,,3
.L88:
	mov	x19, x2
.L81:
	ldp	x5, x2, [x19, 16]
	ldr	w4, [x19, 32]
	cmp	w20, w4
	csel	x2, x2, x5, ge
	csel	w5, wzr, w6, ge
	cbnz	x2, .L88
	mov	x23, x19
	cbnz	w5, .L96
.L82:
	cmp	w20, w4
	ble	.L97
.L83:
	mov	w25, 1
	cmp	x24, x23
	bne	.L98
.L85:
	mov	x0, 40
	bl	_Znwm
	mov	x19, x0
	ldr	w4, [x22]
	mov	x3, x24
	mov	x2, x23
	mov	w0, w25
	mov	x1, x19
	str	w4, [x19, 32]
	bl	_ZSt29_Rb_tree_insert_and_rebalancebPSt18_Rb_tree_node_baseS0_RS_
	ldr	x1, [x21, 40]
	mov	w2, 1
	ldp	x23, x24, [sp, 48]
	add	x1, x1, 1
	str	x1, [x21, 40]
	mov	x1, 0
	ldp	x21, x22, [sp, 32]
	mov	x0, x19
	ldp	x19, x20, [sp, 16]
	bfi	x1, x2, 0, 8
	ldr	x25, [sp, 64]
	ldp	x29, x30, [sp], 80
	.cfi_remember_state
	.cfi_restore 30
	.cfi_restore 29
	.cfi_restore 25
	.cfi_restore 23
	.cfi_restore 24
	.cfi_restore 21
	.cfi_restore 22
	.cfi_restore 19
	.cfi_restore 20
	.cfi_def_cfa_offset 0
	ret
	.p2align 2,,3
.L97:
	.cfi_restore_state
	mov	w2, 0
	mov	x1, 0
	ldp	x21, x22, [sp, 32]
	mov	x0, x19
	ldp	x19, x20, [sp, 16]
	bfi	x1, x2, 0, 8
	ldp	x23, x24, [sp, 48]
	ldr	x25, [sp, 64]
	ldp	x29, x30, [sp], 80
	.cfi_remember_state
	.cfi_restore 30
	.cfi_restore 29
	.cfi_restore 25
	.cfi_restore 23
	.cfi_restore 24
	.cfi_restore 21
	.cfi_restore 22
	.cfi_restore 19
	.cfi_restore 20
	.cfi_def_cfa_offset 0
	ret
	.p2align 2,,3
.L96:
	.cfi_restore_state
	ldr	x0, [x21, 24]
	cmp	x0, x19
	beq	.L83
.L86:
	mov	x0, x19
	mov	x23, x19
	bl	_ZSt18_Rb_tree_decrementPSt18_Rb_tree_node_base
	ldr	w4, [x0, 32]
	mov	x19, x0
	b	.L82
	.p2align 2,,3
.L98:
	ldr	w0, [x23, 32]
	cmp	w20, w0
	cset	w25, lt
	b	.L85
	.p2align 2,,3
.L79:
	ldr	x0, [x0, 24]
	mov	x19, x24
	cmp	x24, x0
	bne	.L86
	mov	x23, x24
	mov	w25, 1
	b	.L85
	.cfi_endproc
.LFE10960:
	.size	_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE16_M_insert_uniqueIRKiEESt4pairISt17_Rb_tree_iteratorIiEbEOT_, .-_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE16_M_insert_uniqueIRKiEESt4pairISt17_Rb_tree_iteratorIiEbEOT_
	.section	.rodata.str1.8,"aMS",@progbits,1
	.align	3
.LC0:
	.string	"Bhinneka"
	.align	3
.LC1:
	.string	"Chaneka"
	.section	.text.startup,"ax",@progbits
	.align	2
	.p2align 4,,11
	.global	main
	.type	main, %function
main:
.LFB9814:
	.cfi_startproc
	stp	x29, x30, [sp, -112]!
	.cfi_def_cfa_offset 112
	.cfi_offset 29, -112
	.cfi_offset 30, -104
	mov	w0, 0
	mov	x29, sp
	stp	x21, x22, [sp, 32]
	.cfi_offset 21, -80
	.cfi_offset 22, -72
	adrp	x21, _ZSt3cin
	add	x21, x21, :lo12:_ZSt3cin
	stp	x25, x26, [sp, 64]
	.cfi_offset 25, -48
	.cfi_offset 26, -40
	adrp	x25, _ZSt4cout
	add	x25, x25, :lo12:_ZSt4cout
	stp	x19, x20, [sp, 16]
	stp	x23, x24, [sp, 48]
	.cfi_offset 19, -96
	.cfi_offset 20, -88
	.cfi_offset 23, -64
	.cfi_offset 24, -56
	bl	_ZNSt8ios_base15sync_with_stdioEb
	adrp	x23, .LANCHOR0
	add	x20, x23, :lo12:.LANCHOR0
	mov	x0, x21
	mov	x1, x20
	str	xzr, [x25, 224]
	str	xzr, [x21, 232]
	bl	_ZNSirsERi
	add	x1, x20, 4
	bl	_ZNSirsERi
	add	x1, x20, 8
	bl	_ZNSirsERi
	ldr	w0, [x23, #:lo12:.LANCHOR0]
	cmp	w0, 1
	ldr	w0, [x20, 4]
	beq	.L147
	cmp	w0, 1
	beq	.L106
	ldr	w0, [x20, 8]
	cmp	w0, 0
	ble	.L108
	adrp	x22, g
	mov	w19, 1
	add	x22, x22, :lo12:g
	mov	w24, 48
	b	.L103
	.p2align 2,,3
.L148:
	ldr	w0, [sp, 108]
	cmp	w0, 1
	beq	.L106
	ldr	w0, [x20, 8]
	cmp	w0, w19
	blt	.L108
.L103:
	add	x1, sp, 104
	mov	x0, x21
	bl	_ZNSirsERi
	add	w19, w19, 1
	add	x1, sp, 108
	bl	_ZNSirsERi
	ldr	w0, [sp, 104]
	add	x1, sp, 108
	smaddl	x0, w0, w24, x22
	bl	_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE16_M_insert_uniqueIRKiEESt4pairISt17_Rb_tree_iteratorIiEbEOT_
	ldr	w0, [sp, 104]
	cmp	w0, 1
	bne	.L148
.L106:
	adrp	x1, .LC1
	mov	x0, x25
	add	x1, x1, :lo12:.LC1
	mov	x2, 7
	bl	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
.L102:
	ldp	x19, x20, [sp, 16]
	mov	w0, 0
	ldp	x21, x22, [sp, 32]
	ldp	x23, x24, [sp, 48]
	ldp	x25, x26, [sp, 64]
	ldp	x29, x30, [sp], 112
	.cfi_remember_state
	.cfi_restore 30
	.cfi_restore 29
	.cfi_restore 25
	.cfi_restore 26
	.cfi_restore 23
	.cfi_restore 24
	.cfi_restore 21
	.cfi_restore 22
	.cfi_restore 19
	.cfi_restore 20
	.cfi_def_cfa_offset 0
	ret
.L147:
	.cfi_restore_state
	cmp	w0, 1
	bne	.L106
	ldr	w0, [x20, 8]
	cbnz	w0, .L106
.L109:
	mov	x0, x25
	adrp	x1, .LC0
	mov	x2, 8
	add	x1, x1, :lo12:.LC0
	bl	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	b	.L102
.L108:
	ldr	w20, [x20, 4]
	ldr	w0, [x23, #:lo12:.LANCHOR0]
	str	w20, [sp, 108]
	cmp	w0, 1
	ble	.L105
	sub	w3, w0, #2
	sxtw	x26, w0
	adrp	x1, g
	add	x1, x1, :lo12:g
	sub	x26, x26, x3
	sub	x2, x1, #40
	mov	w5, 48
	mov	x4, 8
	mov	x3, 48
	adrp	x23, winLine
	smaddl	x0, w0, w5, x4
	adrp	x21, winLine+4
	madd	x26, x26, x3, x2
	add	x23, x23, :lo12:winLine
	add	x19, x0, x1
	add	x21, x21, :lo12:winLine+4
	str	x27, [sp, 80]
	.cfi_offset 27, -32
	.p2align 3,,7
.L120:
	cbz	w20, .L146
	mov	w22, 1
.L119:
	ldr	x0, [x19, 32]
	sub	x27, x19, #8
	cbz	x0, .L110
	mov	x0, x19
	bl	_ZSt18_Rb_tree_decrementPKSt18_Rb_tree_node_base
	ldr	w0, [x0, 32]
	mov	w24, w20
	cmp	w0, w20
	bge	.L111
.L110:
	mov	x0, x27
	add	x1, sp, 108
	sub	w24, w20, #1
	bl	_ZNSt8_Rb_treeIiiSt9_IdentityIiESt4lessIiESaIiEE16_M_insert_uniqueIRKiEESt4pairISt17_Rb_tree_iteratorIiEbEOT_
	str	w24, [sp, 108]
.L111:
	ldr	x0, [x19, 16]
	cmp	x0, x19
	beq	.L115
	.p2align 3,,7
.L112:
	ldrsw	x1, [x0, 32]
	str	w22, [x23, x1, lsl 2]
	bl	_ZSt18_Rb_tree_incrementPKSt18_Rb_tree_node_base
	cmp	x0, x19
	bne	.L112
.L115:
	cmp	w24, 0
	ble	.L149
	sub	w0, w24, #1
	sxtw	x2, w24
	sub	x2, x2, #2
	mov	w3, 0
	sub	x2, x2, w0, uxtw
	sxtw	x0, w0
	b	.L116
	.p2align 2,,3
.L117:
	mov	w20, w0
	sub	x0, x0, #1
	mov	w3, 1
	cmp	x0, x2
	beq	.L118
.L116:
	ldr	w1, [x21, x0, lsl 2]
	cbnz	w1, .L117
	cbz	w3, .L150
.L118:
	str	w20, [sp, 108]
.L114:
	sub	x19, x19, #48
	cmp	x19, x26
	bne	.L120
.L146:
	ldr	x27, [sp, 80]
	.cfi_restore 27
.L105:
	ldr	w0, [sp, 108]
	cmp	w0, 1
	bne	.L106
	b	.L109
.L150:
	.cfi_offset 27, -32
	sub	x19, x19, #48
	cmp	x19, x26
	beq	.L146
	mov	w20, w24
	b	.L119
.L149:
	mov	w20, w24
	b	.L114
	.cfi_endproc
.LFE9814:
	.size	main, .-main
	.align	2
	.p2align 4,,11
	.type	_GLOBAL__sub_I_n, %function
_GLOBAL__sub_I_n:
.LFB11673:
	.cfi_startproc
	adrp	x1, g
	add	x1, x1, :lo12:g
	add	x1, x1, 9596928
	adrp	x0, g+8
	add	x1, x1, 3320
	add	x0, x0, :lo12:g+8
	.p2align 3,,7
.L152:
	str	wzr, [x0]
	stp	xzr, x0, [x0, 8]
	stp	x0, xzr, [x0, 24]
	add	x0, x0, 48
	cmp	x0, x1
	bne	.L152
	adrp	x2, __dso_handle
	adrp	x0, __tcf_0
	add	x2, x2, :lo12:__dso_handle
	add	x0, x0, :lo12:__tcf_0
	mov	x1, 0
	b	__cxa_atexit
	.cfi_endproc
.LFE11673:
	.size	_GLOBAL__sub_I_n, .-_GLOBAL__sub_I_n
	.section	.init_array,"aw"
	.align	3
	.xword	_GLOBAL__sub_I_n
	.global	winLine
	.global	g
	.global	k
	.global	m
	.global	n
	.bss
	.align	4
	.set	.LANCHOR0,. + 0
	.type	n, %object
	.size	n, 4
n:
	.zero	4
	.type	m, %object
	.size	m, 4
m:
	.zero	4
	.type	k, %object
	.size	k, 4
k:
	.zero	4
	.zero	4
	.type	winLine, %object
	.size	winLine, 800020
winLine:
	.zero	800020
	.zero	4
	.type	g, %object
	.size	g, 9600240
g:
	.zero	9600240
	.hidden	__dso_handle
	.ident	"GCC: (GNU) 13.4.0"
	.section	.note.GNU-stack,"",@progbits
