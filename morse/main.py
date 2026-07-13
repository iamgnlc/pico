from machine import Pin
from time import sleep, ticks_ms, ticks_diff

# Morse Code Dictionary
MORSE_CODE_DICT = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    " ": " ",
}

# Timing constants (in seconds)
DOT_DURATION = 0.2
DASH_DURATION = DOT_DURATION * 3
SYMBOL_SPACE = DOT_DURATION
LETTER_SPACE = DOT_DURATION * 3
WORD_SPACE = DOT_DURATION * 7

# Pin setup
led = Pin(2, Pin.OUT)              # External LED for Morse
onboard_led = Pin(25, Pin.OUT)     # Onboard LED (power-on indicator)

start_button = Pin(14, Pin.IN, Pin.PULL_UP)
stop_button = Pin(12, Pin.IN, Pin.PULL_UP)

# Power-on blink (onboard LED)
for _ in range(1):
    onboard_led.on()
    sleep(DOT_DURATION)
    onboard_led.off()
    sleep(DOT_DURATION)

# Global flags
stop_requested = False
last_interrupt_time = 0  # For debouncing

# Interrupt handler for stop button
def stop_isr(pin):
    global stop_requested, last_interrupt_time
    current_time = ticks_ms()
    if ticks_diff(current_time, last_interrupt_time) > 200:
        stop_requested = True
        print("Stop requested (IRQ).")
        last_interrupt_time = current_time

# Attach interrupt
stop_button.irq(trigger=Pin.IRQ_FALLING, handler=stop_isr)

# Interruptible sleep
def sleep_interruptible(duration):
    global stop_requested
    interval = 0.01
    elapsed = 0
    while elapsed < duration:
        if stop_requested:
            break
        sleep(interval)
        elapsed += interval

# Morse blink functions
def blink_dot():
    if stop_requested:
        return
    led.on()
    sleep_interruptible(DOT_DURATION)
    led.off()
    sleep_interruptible(SYMBOL_SPACE)

def blink_dash():
    if stop_requested:
        return
    led.on()
    sleep_interruptible(DASH_DURATION)
    led.off()
    sleep_interruptible(SYMBOL_SPACE)

def blink_morse(morse_code):
    for symbol in morse_code:
        if stop_requested:
            return
        if symbol == ".":
            blink_dot()
        elif symbol == "-":
            blink_dash()
        else:
            sleep_interruptible(WORD_SPACE - SYMBOL_SPACE)
    sleep_interruptible(LETTER_SPACE - SYMBOL_SPACE)

# Remove unsupported characters and blink Morse
def text_to_morse(text):
    allowed_chars = MORSE_CODE_DICT.keys()
    clean_text = "".join(c for c in text.upper() if c in allowed_chars)

    for char in clean_text:
        if stop_requested:
            return
        blink_morse(MORSE_CODE_DICT[char])

# Main loop
try:
    while True:
        if not start_button.value():  # Start button pressed
            stop_requested = False
            print("Starting Morse...")
            with open("morse.txt", "r") as file:
                phrase = file.read()
                text_to_morse(phrase)
            print("Done.")
            sleep(0.5)  # Debounce
finally:
    led.off()
    onboard_led.off()
