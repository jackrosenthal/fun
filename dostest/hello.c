#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <dos.h>

#include "scancodes.h"

uint8_t inb(uint16_t port);
#pragma aux inb =				\
	"xor eax, eax"				\
	"in al, dx"				\
	parm [ dx ];

void outb(uint8_t byte, uint16_t port);
#pragma aux outb =				\
	"out dx, al"				\
	parm [ al ] [ dx ];			\

uint8_t get_ah(void);
#pragma aux get_ah =				\
	value [ ah ];

void set_ax(uint16_t val);
#pragma aux set_ax =				\
	parm [ ax ];

void wait_irq(void);
#pragma aux wait_irq =				\
	"sti"					\
	"hlt"					\
	"cli"					\
	"cld"					;

#pragma aux iret = "iret";

#define PORT_PS2_DATA          0x0060
#define PORT_PS2_STATUS        0x0064

// Standard commands.
#define I8042_CMD_CTL_RCTR      0x0120
#define I8042_CMD_CTL_WCTR      0x1060
#define I8042_CMD_CTL_TEST      0x01aa

#define I8042_CMD_KBD_TEST      0x01ab
#define I8042_CMD_KBD_DISABLE   0x00ad
#define I8042_CMD_KBD_ENABLE    0x00ae

#define I8042_CMD_AUX_DISABLE   0x00a7
#define I8042_CMD_AUX_ENABLE    0x00a8
#define I8042_CMD_AUX_SEND      0x10d4

// Keyboard commands
#define ATKBD_CMD_SETLEDS       0x10ed
#define ATKBD_CMD_SSCANSET      0x10f0
#define ATKBD_CMD_GETID         0x02f2
#define ATKBD_CMD_ENABLE        0x00f4
#define ATKBD_CMD_RESET_DIS     0x00f5
#define ATKBD_CMD_RESET_BAT     0x01ff

// Mouse commands
#define PSMOUSE_CMD_SETSCALE11  0x00e6
#define PSMOUSE_CMD_SETSCALE21  0x00e7
#define PSMOUSE_CMD_SETRES      0x10e8
#define PSMOUSE_CMD_GETINFO     0x03e9
#define PSMOUSE_CMD_GETID       0x02f2
#define PSMOUSE_CMD_SETRATE     0x10f3
#define PSMOUSE_CMD_ENABLE      0x00f4
#define PSMOUSE_CMD_DISABLE     0x00f5
#define PSMOUSE_CMD_RESET_BAT   0x02ff

// Status register bits.
#define I8042_STR_PARITY        0x80
#define I8042_STR_TIMEOUT       0x40
#define I8042_STR_AUXDATA       0x20
#define I8042_STR_KEYLOCK       0x10
#define I8042_STR_CMDDAT        0x08
#define I8042_STR_MUXERR        0x04
#define I8042_STR_IBF           0x02
#define I8042_STR_OBF           0x01

// Control register bits.
#define I8042_CTR_KBDINT        0x01
#define I8042_CTR_AUXINT        0x02
#define I8042_CTR_IGNKEYLOCK    0x08
#define I8042_CTR_KBDDIS        0x10
#define I8042_CTR_AUXDIS        0x20
#define I8042_CTR_XLATE         0x40

#define I8042_CTL_TIMEOUT       10000

#define I8042_BUFFER_SIZE       16

static int i8042_wait_read(void)
{
	/* dprintf(7, "i8042_wait_read\n"); */
	int i;
	uint8_t status;

	for (i=0; i<I8042_CTL_TIMEOUT; i++) {
		status = inb(PORT_PS2_STATUS);
		if (status & I8042_STR_OBF)
			return 0;
		delay(1);
	}
	 /* warn_timeout(); */
	 return -1;
}

static int
i8042_wait_write(void)
{
	/* dprintf(7, "i8042_wait_write\n"); */
	int i;
	uint8_t status;

	for (i=0; i<I8042_CTL_TIMEOUT; i++) {
		status = inb(PORT_PS2_STATUS);
		if (! (status & I8042_STR_IBF))
			return 0;
		delay(1);
	}
	/* warn_timeout(); */
	return -1;
}

static int i8042_command(int command, char *param)
{
	int receive = (command >> 8) & 0xf;
	int send = (command >> 12) & 0xf;
	int i;
	int ret;

	// Send the command.
	ret = i8042_wait_write();
	if (ret)
		return ret;
	outb(command, PORT_PS2_STATUS);

	// Send parameters (if any).
	for (i = 0; i < send; i++) {
		ret = i8042_wait_write();
		if (ret)
			return ret;
		outb(param[i], PORT_PS2_DATA);
	}

	// Receive parameters (if any).
	for (i = 0; i < receive; i++) {
		ret = i8042_wait_read();
		if (ret)
			return ret;
		param[i] = inb(PORT_PS2_DATA);
		/* dprintf(7, "i8042 param=%x\n", param[i]); */
	}

	return 0;
}

enum mod_flags {
	MOD_SHIFT = (1 << 0),
	MOD_SYM = (1 << 1),
	MOD_CUR = (1 << 2),
	MOD_CTRL = (1 << 3),
	MOD_ALT = (1 << 4),
};

static int get_mod(uint8_t scancode)
{
	scancode = scancode & 0x7F;

	switch (scancode) {
	case KEY_LEFTSHIFT:
	case KEY_RIGHTSHIFT:
		return MOD_SHIFT;
	case KEY_APOSTROPHE:
		return MOD_SYM;
	case KEY_SLASH:
		return MOD_CUR;
	case KEY_LEFTCTRL:
		return MOD_CTRL;
	case KEY_LEFTALT:
		return MOD_ALT;
	}

	return 0;
}
#define BKSP 0x08
#define TAB 0x09
#define ESC 0x1B
#define PAGE_UP 0x21
#define PAGE_DOWN 0x22
#define HOME 0x23
#define END 0x24
#define LEFT 0x25
#define UP 0x26
#define RIGHT 0x27
#define DOWN 0x28
#define DELETE 0x2E

static struct {
	char normal_layer;
	char shift_layer;
	char sym_layer;
	char cur_layer;
} keytab[0x80] = {
	[KEY_ESC] = { ESC },
	[KEY_1] = { '1' },
	[KEY_2] = { '2' },
	[KEY_3] = { '3' },
	[KEY_4] = { '4' },
	[KEY_5] = { '5' },
	[KEY_6] = { '6' },
	[KEY_7] = { '7' },
	[KEY_8] = { '8' },
	[KEY_9] = { '9' },
	[KEY_0] = { '0' },
	[KEY_BACKSPACE] = { BKSP },
	[KEY_TAB] = { ESC },
	[KEY_Q] = { 'q', 'Q', '"', PAGE_UP },
	[KEY_W] = { 'f', 'F', '_', BKSP },
	[KEY_E] = { 'u', 'U', '[', UP },
	[KEY_R] = { 'y', 'Y', ']', DELETE },
	[KEY_T] = { 'z', 'Z', '^', PAGE_DOWN },
	[KEY_Y] = { 'x', 'X', '!' },
	[KEY_U] = { 'k', 'K', '<', '1' },
	[KEY_I] = { 'c', 'C', '>', '2' },
	[KEY_O] = { 'w', 'W', '=', '3' },
	[KEY_P] = { 'b', 'B', '&' },
	[KEY_CAPSLOCK] = { TAB },
	[KEY_LEFTWIN] = { TAB },
	[KEY_A] = { 'o', 'O', '/', HOME },
	[KEY_S] = { 'h', 'H', '-', LEFT },
	[KEY_D] = { 'e', 'E', '{', DOWN },
	[KEY_F] = { 'a', 'A', '}', RIGHT },
	[KEY_G] = { 'i', 'I', '*', END },
	[KEY_H] = { 'd', 'D', '?' },
	[KEY_J] = { 'r', 'R', '(', '4' },
	[KEY_K] = { 't', 'T', ')', '5' },
	[KEY_L] = { 'n', 'N', '\'', '6' },
	[KEY_SEMICOLON] = { 's', 'S', ':' },
	[KEY_Z] = { ',', ',', '#' },
	[KEY_X] = { 'm', 'M', '$' },
	[KEY_C] = { '.', '.', '|' },
	[KEY_V] = { 'j', 'J', '~' },
	[KEY_B] = { ';', ';', '`' },
	[KEY_N] = { 'g', 'G', '+', '0' },
	[KEY_M] = { 'l', 'L', '%', '7' },
	[KEY_COMMA] = { 'p', 'P', '\\', '8' },
	[KEY_DOT] = { 'v', 'V', '@', '9' },
	[KEY_SPACE] = { ' ' },
	[KEY_UP] = { UP },
	[KEY_LEFT] = { LEFT },
	[KEY_RIGHT] = { RIGHT },
	[KEY_DOWN] = { DOWN },
};

static char transkey(uint8_t scancode, int modstate)
{
	char sym;

	scancode = scancode & 0x7F;
	sym = keytab[scancode].normal_layer;

	if ((modstate & MOD_SHIFT) && keytab[scancode].shift_layer)
		sym = keytab[scancode].shift_layer;
	if ((modstate & MOD_SYM) && keytab[scancode].sym_layer)
		sym = keytab[scancode].sym_layer;
	if ((modstate & MOD_CUR) && keytab[scancode].cur_layer)
		sym = keytab[scancode].cur_layer;
	if ((modstate & MOD_CTRL)) {
		if (sym >= 'a' && sym <= 'z')
			sym = 1 + sym - 'a';
		else if (sym >= 'A' && sym <= 'Z')
			sym = 1 + sym - 'A';
	}

	return sym;
}

static uint16_t next_kbd_read;

static void process_scancode(uint8_t scancode)
{
	static int modstate = 0;
	bool released;
	int modkey = 0;
	char letter;

	//printf("process_scancode 0x%02X\n", scancode);

	released = !!(scancode & 0x80);
	modkey = get_mod(scancode);

	if (modkey) {
		//printf("modkey=0x%02X\n", modkey);
		if (released)
			modstate &= ~modkey;
		else
			modstate |= modkey;
		return;
	}

	if (released)
		return;

	if ((modstate & MOD_CTRL) && (modstate & MOD_ALT) && scancode == KEY_DELETE) {
		printf("TODO handle CTRL+ALT+DELETE\n");
		return;
	}

	letter = transkey(scancode, modstate);
	printf("letter=0x%02X ('%c')\n", letter, letter);
	if (!letter)
		return;
	next_kbd_read = (scancode << 8) | letter;
	printf("KEY SET\n");
}

static void _WCINTERRUPT _WCFAR handle_int9(void)
{
	// read key from keyboard controller
	uint8_t val;

	val = inb(PORT_PS2_STATUS);
	val = inb(PORT_PS2_DATA);

	process_scancode(val);

	i8042_command(I8042_CMD_KBD_ENABLE, NULL);
	outb(0x20, 0x20);
}

uint16_t int16_c(int16_t ax)
{
	uint16_t kbd_read;

	printf("int16 AX=%04X\n", ax);

	switch (ax >> 8) {
	case 0x00:
	case 0x10:
		printf("here\n");
		while (!next_kbd_read) {
			printf("next_kbd_read=%04X\n", next_kbd_read);
			wait_irq();
		}
		printf("read key %04X\n", next_kbd_read);
		kbd_read = next_kbd_read;
		next_kbd_read = 0;
		return kbd_read;
	}

	return 0;
}

extern void int16h(void);

int main() {
	char c;

	_dos_setvect(0x9, handle_int9);
	_dos_setvect(0x16, int16h);
	//_dos_keep(0, 16384);
	while (1) {
		c = getchar();
		printf("CHR=%d ('%c')\n", c, c);
	}
	return 42;
}
