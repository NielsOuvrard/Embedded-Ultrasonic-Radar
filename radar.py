import pygame
import serial
import glob
import sys

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
            # Just check if we can open it
            s = serial.Serial(port, 9600, timeout=1)
            s.close()
            return port
        except (OSError, serial.SerialException):
            pass
    
    return None

# Initialize pygame
pygame.init()

MAX_RECTANGLES = 20
proximities_values = [0 for _ in range(MAX_RECTANGLES)]

# Set up the display
width, height = 1920, 1080
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Serial Data Display")

# Set up fonts
font = pygame.font.SysFont('Arial', 72, bold=True)

# Set up colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

def main():
    # Find USB serial port
    port = find_usb_serial_port()
    if not port:
        print("No USB serial port found.")
        pygame.quit()
        sys.exit()
    
    print(f"Connecting to {port}")
    
    # Connect to the serial port
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        print(f"Connected to {port}")
    except serial.SerialException as e:
        print(f"Error connecting to {port}: {e}")
        pygame.quit()
        sys.exit()
    
    distance = 0
    rotation = 0 # between 0 and 1
    selected_rect = 0
    
    # Set up rectangles
    num_rectangles = MAX_RECTANGLES
    rect_width = (width - 20) // MAX_RECTANGLES
    rect_spacing = 0
    max_rect_height = height * 0.8  # 80% of the screen height
    
    running = True
    

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Try to read data from serial
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                print(f"Received: {line}")
                
                # Check if the line matches our expected format
                if ',' in line:
                    try:
                        parts = line.split(',')
                        distance = int(parts[0])
                        rotation = ((int(parts[1]) - 500) / 2000) * (MAX_RECTANGLES)

                        rotation = max(0, min(MAX_RECTANGLES - 1, rotation)) # Clamp to 0-MAX_RECTANGLES
                        selected_rect = int(rotation)

                        # Calculate rectangle height based on distance (scale to fit the screen)
                        # Distance range is 0-25, so we scale it to use most of the screen height
                        proximities_values[selected_rect] = (distance / 25.0) * max_rect_height

                    except (ValueError, IndexError) as e:
                        print(f"Error parsing values: {e}")
        except Exception as e:
            print(f"Error reading from serial: {e}")
        
        # Clear the screen
        screen.fill(BLACK)


        
        
        # Draw the rectangles
        for i in range(num_rectangles):
            rect_x = 10 + i * (rect_width + rect_spacing)
            
            # Calculate base position (bottom of rectangle)
            rect_y = height - 20
            
            # Rectangle dimensions
            rect_h = max(5, proximities_values[i])  # Minimum height of 5 pixels
            
            # Determine rectangle color
            if i == selected_rect:
                color = RED  # Highlight the selected rectangle
            else:
                color = BLUE
            
            # Draw the rectangle
            pygame.draw.rect(screen, color, (rect_x, rect_y - rect_h, rect_width, rect_h))
            
            # Draw a thin border around each rectangle
            pygame.draw.rect(screen, WHITE, (rect_x, rect_y - rect_h, rect_width, rect_h), 1)
        

        # Draw information text
        distance_text = font.render(f"Distance: {distance}", True, WHITE)
        rotation_text = font.render(f"Rotation: {rotation:.1f}", True, WHITE)
        selected_text = font.render(f"Selected Rectangle: {selected_rect}", True, WHITE)
        
        screen.blit(distance_text, (10, 10))
        screen.blit(rotation_text, (10, 80))
        screen.blit(selected_text, (10, 160))

        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        pygame.time.delay(50)
    
    # Clean up
    ser.close()
    pygame.quit()

if __name__ == "__main__":
    main()