import pygame
import serial
import glob
import sys
import threading
import queue

# Function to find the first USB serial port
def find_usb_serial_port():
    if sys.platform.startswith('darwin'):  # macOS
        ports = glob.glob('/dev/tty.usbmodem*')
    elif sys.platform.startswith('linux'):  # Linux
        ports = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
    elif sys.platform.startswith('win'):  # Windows
        ports = ['COM%s' % (i + 1) for i in range(256)]
    else:
        print(f"Unsupported platform: {sys.platform}")
        return None
    
    for port in ports:
        try:
            print(f"Trying port: {port}")
            s = serial.Serial(port, 9600, timeout=1)
            s.close()
            return port
        except (OSError, serial.SerialException):
            pass
    
    return None

def serial_reader(ser, data_queue, stop_event):
    while not stop_event.is_set():
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                data_queue.put(line)
        except Exception as e:
            print(f"Error reading from serial: {e}")

def clean_unused_rectangles(proximities_values):
    for i in range(1, len(proximities_values) - 1):
        if proximities_values[i - 1] != 0 and proximities_values[i] == 0 and proximities_values[i + 1] != 0:
            proximities_values[i] = (proximities_values[i - 1] + proximities_values[i + 1]) / 2
    return proximities_values

def main():
    pygame.init()

    MAX_RECTANGLES = 100
    proximities_values = [0 for _ in range(MAX_RECTANGLES)]
    width, height = 1920, 1080
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Serial Data Display")
    font = pygame.font.SysFont('Arial', 72, bold=True)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    BLUE = (0, 0, 255)
    RED = (255, 0, 0)

    # Find USB serial port
    port = find_usb_serial_port()
    if not port:
        print("No USB serial port found.")
        pygame.quit()
        sys.exit()
    
    print(f"Connecting to {port}")
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        print(f"Connected to {port}")
    except serial.SerialException as e:
        print(f"Error connecting to {port}: {e}")
        pygame.quit()
        sys.exit()
    
    distance = 0
    rotation = 0
    selected_rect = 0

    num_rectangles = MAX_RECTANGLES
    rect_width = (width - 20) // MAX_RECTANGLES
    rect_spacing = 0
    max_rect_height = height * 0.8

    # Threading setup
    data_queue = queue.Queue()
    stop_event = threading.Event()
    reader_thread = threading.Thread(target=serial_reader, args=(ser, data_queue, stop_event))
    reader_thread.daemon = True
    reader_thread.start()

    running = True
    index_debug = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Process all new serial lines
        while not data_queue.empty():
            line = data_queue.get()
            print(f"Received: {line}")
            if ',' in line:
                try:
                    parts = line.split(',')
                    distance = int(parts[0])
                    rotation = ((int(parts[1]) - 500) / 2000) * (MAX_RECTANGLES)
                    rotation = max(0, min(MAX_RECTANGLES - 1, rotation))
                    selected_rect = int(rotation)
                    proximities_values[selected_rect] = (distance / 50.0) * max_rect_height
                except (ValueError, IndexError) as e:
                    print(f"Error parsing values: {e}")

        # Clean unused rectangles
        proximities_values = clean_unused_rectangles(proximities_values)

        if index_debug % 100 == 0:
            print(f"\n\n{proximities_values}\n\n")

        # Clear the screen
        screen.fill(BLACK)

        # Draw the rectangles
        for i in range(num_rectangles):
            rect_x = 10 + i * (rect_width + rect_spacing)
            rect_y = height - 20
            rect_h = max(5, proximities_values[i])
            color = RED if i == selected_rect else BLUE
            pygame.draw.rect(screen, color, (rect_x, rect_y - rect_h, rect_width, rect_h))
            pygame.draw.rect(screen, WHITE, (rect_x, rect_y - rect_h, rect_width, rect_h), 1)

        # Draw information text
        distance_text = font.render(f"Distance: {distance}", True, WHITE)
        rotation_text = font.render(f"Rotation: {rotation:.1f}", True, WHITE)
        selected_text = font.render(f"Selected Rectangle: {selected_rect}", True, WHITE)
        screen.blit(distance_text, (10, 10))
        screen.blit(rotation_text, (10, 80))
        screen.blit(selected_text, (10, 160))

        pygame.display.flip()
        pygame.time.delay(50)

        index_debug += 1

    # Clean up
    stop_event.set()
    reader_thread.join(timeout=1)
    ser.close()
    pygame.quit()

if __name__ == "__main__":
    main()
