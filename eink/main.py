from machine import Pin, SPI
import framebuf
import utime


EPD_WIDTH       = 122
EPD_HEIGHT      = 250

RST_PIN         = 12
DC_PIN          = 8
CS_PIN          = 9
BUSY_PIN        = 13

# ---- user config -----------------------------------------------------------
# Lines of text to display (one entry per line).
LINES       = ["GNLC","&", "GINTARE"]

# Character size multiplier. Each character is 8x8 at scale=1.
TEXT_SCALE  = 8

# Extra vertical pixels between lines.
LINE_GAP    = 12

# False = black text on white background.
# True  = white text on black background.
INVERT      = False
# ---------------------------------------------------------------------------

# Visible drawing area for the landscape framebuffer.
# The Waveshare driver pads the short axis from 122 -> 128 to align on 8-bit
# byte boundaries, and the 6 padded rows sit at y = 0..5 (off-glass).
# Visible pixels are y = Y_OFFSET .. Y_OFFSET + CANVAS_H - 1.
CANVAS_W    = 250
CANVAS_H    = 122
Y_OFFSET    = 128 - CANVAS_H   # = 6

class EPD_2in13_V4_Portrait(framebuf.FrameBuffer):
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        if EPD_WIDTH % 8 == 0:
            self.width = EPD_WIDTH
        else :
            self.width = (EPD_WIDTH // 8) * 8 + 8
        self.height = EPD_HEIGHT

        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_HLSB)
        self.init()
    
    '''
    function :Change the pin state
    parameter:
        pin : pin
        value : state
    '''
    def digital_write(self, pin, value):
        pin.value(value)

    '''
    function : Read the pin state 
    parameter:
        pin : pin
    '''
    def digital_read(self, pin):
        return pin.value()

    '''
    function : The time delay function
    parameter:
        delaytime : ms
    '''
    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)
        
    '''
    function : Write data to SPI
    parameter:
        data : data
    '''
    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    '''
    function :Hardware reset
    parameter:
    '''
    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)   

    '''
    function :send command
    parameter:
     command : Command register
    '''
    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)
    
    '''
    function :send data
    parameter:
     data : Write data
    '''
    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)
        
    def send_data1(self, buf):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi.write(bytearray(buf))
        self.digital_write(self.cs_pin, 1)
    
    '''
    function :Wait until the busy_pin goes LOW
    parameter:
    '''
    def ReadBusy(self):
        print('busy')
        self.delay_ms(10)
        while(self.digital_read(self.busy_pin) == 1):      # 0: idle, 1: busy
            self.delay_ms(10)    
        print('busy release')
    
    '''
    function : Turn On Display
    parameter:
    '''
    def TurnOnDisplay(self):
        self.send_command(0x22) # Display Update Control
        self.send_data(0xf7)
        self.send_command(0x20) # Activate Display Update Sequence
        self.ReadBusy()

    '''
    function : Turn On Display Fast
    parameter:
    '''
    def TurnOnDisplay_Fast(self):
        self.send_command(0x22) # Display Update Control
        self.send_data(0xC7)    # fast:0x0c, quality:0x0f, 0xcf
        self.send_command(0x20) # Activate Display Update Sequence
        self.ReadBusy()
    
    '''
    function : Turn On Display Part
    parameter:
    '''
    def TurnOnDisplayPart(self):
        self.send_command(0x22) # Display Update Control
        self.send_data(0xff)    # fast:0x0c, quality:0x0f, 0xcf
        self.send_command(0x20) # Activate Display Update Sequence
        self.ReadBusy()
    
    '''
    function : Setting the display window
    parameter:
        Xstart : X-axis starting position
        Ystart : Y-axis starting position
        Xend : End position of X-axis
        Yend : End position of Y-axis
    '''
    def SetWindows(self, Xstart, Ystart, Xend, Yend):
        self.send_command(0x44)                #  SET_RAM_X_ADDRESS_START_END_POSITION
        self.send_data((Xstart >> 3) & 0xFF)
        self.send_data((Xend >> 3) & 0xFF)
        
        self.send_command(0x45)                #  SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)
        self.send_data(Yend & 0xFF)
        self.send_data((Yend >> 8) & 0xFF)
        
    '''
    function : Set Cursor
    parameter:
        Xstart : X-axis starting position
        Ystart : Y-axis starting position
    '''
    def SetCursor(self, Xstart, Ystart):
        self.send_command(0x4E)             #  SET_RAM_X_ADDRESS_COUNTER
        self.send_data(Xstart & 0xFF)
        
        self.send_command(0x4F)             #  SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)

    '''
    function : Initialize the e-Paper register
    parameter:
    '''
    def init(self):
        print('init')
        self.reset()
        self.delay_ms(100)
        
        self.ReadBusy()
        self.send_command(0x12)  # SWRESET
        self.ReadBusy()
        
        self.send_command(0x01)  # Driver output control 
        self.send_data(0xf9)
        self.send_data(0x00)
        self.send_data(0x00)
        
        self.send_command(0x11)  #data entry mode 
        self.send_data(0x03)
        
        self.SetWindows(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)
        
        self.send_command(0x3C)  # BorderWaveform
        self.send_data(0x05)
        
        self.send_command(0x21) # Display update control
        self.send_data(0x00)
        self.send_data(0x80)
        
        self.send_command(0x18) # Read built-in temperature sensor
        self.send_data(0x80)
        
        self.ReadBusy()
        
    '''
    function : Initialize the e-Paper fast register
    parameter:
    '''
    def init_fast(self):
        print('init_fast')
        self.reset()
        self.delay_ms(100)

        self.send_command(0x12)  #SWRESET
        self.ReadBusy() 

        self.send_command(0x18) # Read built-in temperature sensor
        self.send_command(0x80)

        self.send_command(0x11) # data entry mode       
        self.send_data(0x03)    

        self.SetWindow(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)
        
        self.send_command(0x22) # Load temperature value
        self.send_data(0xB1)
        self.send_command(0x20)
        self.ReadBusy()

        self.send_command(0x1A) # Write to temperature register
        self.send_data(0x64)
        self.send_data(0x00)
                        
        self.send_command(0x22) # Load temperature value
        self.send_data(0x91)
        self.send_command(0x20)
        self.ReadBusy()
        
        return 0
       
    '''
    function : Clear screen
    parameter:
    '''
    def Clear(self):
        self.send_command(0x24)
        self.send_data1([0xff] * self.height * int(self.width / 8))
                
        self.TurnOnDisplay()    
    
    '''
    function : Sends the image buffer in RAM to e-Paper and displays
    parameter:
        image : Image data
    '''
    def display(self, image):
        self.send_command(0x24)
        self.send_data1(image) 
        self.TurnOnDisplay()
    
    def display_fast(self, image):
        self.send_command(0x24)
        self.send_data2(image) 
        self.TurnOnDisplay_Fast()
    
    '''
    function : Refresh a base image
    parameter:
        image : Image data
    '''
    def Display_Base(self, image):
        self.send_command(0x24)
        self.send_data1(image)
                
        self.send_command(0x26)
        self.send_data1(image)
                
        self.TurnOnDisplay()
        
    '''
    function : Sends the image buffer in RAM to e-Paper and partial refresh
    parameter:
        image : Image data
    '''    
    def displayPartial(self, image):
        self.reset()

        self.send_command(0x3C) # BorderWavefrom
        self.send_data(0x80)

        self.send_command(0x01) # Driver output control      
        self.send_data(0xF9) 
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x11) # data entry mode       
        self.send_data(0x03)

        self.SetWindows(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)
        
        self.send_command(0x24) # WRITE_RAM
        self.send_data1(image)  
        self.TurnOnDisplayPart()
    
    '''
    function : Enter sleep mode
    parameter:
    '''
    def sleep(self):
        self.send_command(0x10) #enter deep sleep
        self.send_data(0x01)
        self.delay_ms(100)
        

class EPD_2in13_V4_Landscape(framebuf.FrameBuffer):
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        if EPD_WIDTH % 8 == 0:
            self.width = EPD_WIDTH
        else :
            self.width = (EPD_WIDTH // 8) * 8 + 8

        self.height = EPD_HEIGHT
        
        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.height, self.width, framebuf.MONO_VLSB)
        self.init()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)   

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)
        
    def send_data1(self, buf):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi.write(bytearray(buf))
        self.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        print('busy')
        self.delay_ms(10)
        while(self.digital_read(self.busy_pin) == 1):      # 0: idle, 1: busy
            self.delay_ms(10)    
        print('busy release')

    '''
    function : Turn On Display
    parameter:
    '''
    def TurnOnDisplay(self):
        self.send_command(0x22) # Display Update Control
        self.send_data(0xf7)
        self.send_command(0x20) # Activate Display Update Sequence
        self.ReadBusy()

    '''
    function : Turn On Display Fast
    parameter:
    '''
    def TurnOnDisplay_Fast(self):
        self.send_command(0x22) # Display Update Control
        self.send_data(0xC7)    # fast:0x0c, quality:0x0f, 0xcf
        self.send_command(0x20) # Activate Display Update Sequence
        self.ReadBusy()
    
    '''
    function : Turn On Display Part
    parameter:
    '''
    def TurnOnDisplayPart(self):
        self.send_command(0x22) # Display Update Control
        self.send_data(0xff)    # fast:0x0c, quality:0x0f, 0xcf
        self.send_command(0x20) # Activate Display Update Sequence
        self.ReadBusy()
    
    '''
    function : Setting the display window
    parameter:
        Xstart : X-axis starting position
        Ystart : Y-axis starting position
        Xend : End position of X-axis
        Yend : End position of Y-axis
    '''
    def SetWindows(self, Xstart, Ystart, Xend, Yend):
        self.send_command(0x44)                #  SET_RAM_X_ADDRESS_START_END_POSITION
        self.send_data((Xstart >> 3) & 0xFF)
        self.send_data((Xend >> 3) & 0xFF)
        
        self.send_command(0x45)                #  SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)
        self.send_data(Yend & 0xFF)
        self.send_data((Yend >> 8) & 0xFF)
        
    '''
    function : Set Cursor
    parameter:
        Xstart : X-axis starting position
        Ystart : Y-axis starting position
    '''
    def SetCursor(self, Xstart, Ystart):
        self.send_command(0x4E)             #  SET_RAM_X_ADDRESS_COUNTER
        self.send_data(Xstart & 0xFF)
        
        self.send_command(0x4F)             #  SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)

    '''
    function : Initialize the e-Paper register
    parameter:
    '''
    def init(self):
        print('init')
        self.reset()
        self.delay_ms(100)
        
        self.ReadBusy()
        self.send_command(0x12)  # SWRESET
        self.ReadBusy()
        
        self.send_command(0x01)  # Driver output control 
        self.send_data(0xf9)
        self.send_data(0x00)
        self.send_data(0x00)
        
        self.send_command(0x11)  #data entry mode 
        self.send_data(0x07)
        
        self.SetWindows(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)
        
        self.send_command(0x3C)  # BorderWaveform
        self.send_data(0x05)
        
        self.send_command(0x21) # Display update control
        self.send_data(0x00)
        self.send_data(0x80)
        
        self.send_command(0x18) # Read built-in temperature sensor
        self.send_data(0x80)
        
        self.ReadBusy()
        
    '''
    function : Initialize the e-Paper fast register
    parameter:
    '''
    def init_fast(self):
        print('init_fast')
        self.reset()
        self.delay_ms(100)

        self.send_command(0x12)  #SWRESET
        self.ReadBusy() 

        self.send_command(0x18) # Read built-in temperature sensor
        self.send_command(0x80)

        self.send_command(0x11) # data entry mode       
        self.send_data(0x07)    

        self.SetWindow(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)
        
        self.send_command(0x22) # Load temperature value
        self.send_data(0xB1)
        self.send_command(0x20)
        self.ReadBusy()

        self.send_command(0x1A) # Write to temperature register
        self.send_data(0x64)
        self.send_data(0x00)
                        
        self.send_command(0x22) # Load temperature value
        self.send_data(0x91)
        self.send_command(0x20)
        self.ReadBusy()
        
        return 0
       
    '''
    function : Clear screen
    parameter:
    '''
    def Clear(self):
        self.send_command(0x24)
        self.send_data1([0xff] * self.height * int(self.width / 8))
                
        self.TurnOnDisplay()    
    
    '''
    function : Sends the image buffer in RAM to e-Paper and displays
    parameter:
        image : Image data
    '''
    def display(self, image):
        self.send_command(0x24)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])
        self.TurnOnDisplay()
    
    def display_fast(self, image):
        self.send_command(0x24)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])
        self.TurnOnDisplay_Fast()
    
    '''
    function : Refresh a base image
    parameter:
        image : Image data
    '''
    def Display_Base(self, image):
        self.send_command(0x24)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])
                
        self.send_command(0x26)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])
                
        self.TurnOnDisplay()
        
    '''
    function : Sends the image buffer in RAM to e-Paper and partial refresh
    parameter:
        image : Image data
    '''    
    def displayPartial(self, image):
        self.reset()

        self.send_command(0x3C) # BorderWavefrom
        self.send_data(0x80)

        self.send_command(0x01) # Driver output control      
        self.send_data(0xF9) 
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x11) # data entry mode       
        self.send_data(0x07)

        self.SetWindows(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)
        
        self.send_command(0x24) # WRITE_RAM
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])
        self.TurnOnDisplayPart()
    
    '''
    function : Enter sleep mode
    parameter:
    '''
    def sleep(self):
        self.send_command(0x10) #enter deep sleep
        self.send_data(0x01)
        self.delay_ms(100)
        
        
def _render_text(s):
    # Render s into an 8-row temp framebuf and return (buf, width, top, bottom)
    # where top/bottom are the first/last rows that actually contain ink.
    w = 8 * len(s)
    tmp_buf = bytearray(((w + 7) // 8) * 8)
    tmp = framebuf.FrameBuffer(tmp_buf, w, 8, framebuf.MONO_HLSB)
    tmp.fill(0)
    tmp.text(s, 0, 0, 1)
    top, bottom = 8, -1
    for cy in range(8):
        for cx in range(w):
            if tmp.pixel(cx, cy):
                if cy < top:
                    top = cy
                bottom = cy
                break
    if bottom < 0:
        top, bottom = 0, 7
    return tmp, w, top, bottom


def big_text(fb, s, x, y, color, scale):
    # Draw s at (x, y) so that y aligns with the top of the actual ink,
    # not the top of the empty 8-row cell.
    tmp, w, top, _ = _render_text(s)
    for cy in range(8):
        for cx in range(w):
            if tmp.pixel(cx, cy):
                fb.fill_rect(x + cx * scale,
                             y + (cy - top) * scale,
                             scale, scale, color)


def text_height(s, scale):
    _, _, top, bottom = _render_text(s)
    return (bottom - top + 1) * scale


def fit_scale(lines, gap, canvas_w, canvas_h, requested):
    """Largest integer scale <= requested such that the block of lines
    fits within canvas_w x canvas_h. Never returns less than 1."""
    if not lines:
        return max(1, requested)
    max_len = max(len(s) for s in lines) or 1
    w_scale = canvas_w // (8 * max_len)

    unit_h = sum(text_height(s, 1) for s in lines)
    remaining_h = canvas_h - gap * (len(lines) - 1)
    if unit_h <= 0 or remaining_h <= 0:
        h_scale = 1
    else:
        h_scale = remaining_h // unit_h

    return max(1, min(requested, w_scale, h_scale))


if __name__=='__main__':
    epd = EPD_2in13_V4_Landscape()
    # Skip epd.Clear() — it would do an extra white-flash refresh before
    # the content refresh. The single display() below is enough to draw
    # the final frame from whatever RAM state the panel powered up in.

    bg = 0x00 if INVERT else 0xFF
    fg = 0xFF if INVERT else 0x00

    # Panel border (physical inactive area around the glass) is controlled
    # by the SSD1680 Border Waveform register (0x3C). init() sets it to
    # 0x05 = white; override so the border always matches the background.
    epd.send_command(0x3C)
    epd.send_data(0x00 if INVERT else 0x05)   # 0x00 = black, 0x05 = white

    epd.fill(bg)

    # Auto-shrink TEXT_SCALE so the widest line fits horizontally AND the
    # full block fits vertically. Only shrinks — never grows past TEXT_SCALE.
    scale = fit_scale(LINES, LINE_GAP, CANVAS_W, CANVAS_H, TEXT_SCALE)

    heights = [text_height(s, scale) for s in LINES]
    block_h = sum(heights) + LINE_GAP * (len(LINES) - 1)
    y       = Y_OFFSET + (CANVAS_H - block_h) // 2

    for s, h in zip(LINES, heights):
        text_w = 8 * len(s) * scale
        x = (CANVAS_W - text_w) // 2
        big_text(epd, s, x, y, fg, scale)
        y += h + LINE_GAP

    epd.display(epd.buffer)
    

