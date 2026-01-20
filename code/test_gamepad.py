#!/usr/bin/env python3
"""
Test Gamepad/Controller Input

Run this to see what buttons map to what numbers on your controller.
"""

import sys

try:
    import pygame
except ImportError:
    print("pygame not installed. Run: pip install pygame")
    sys.exit(1)


def main():
    pygame.init()
    pygame.joystick.init()

    joystick_count = pygame.joystick.get_count()

    if joystick_count == 0:
        print("No gamepad/controller detected!")
        print("Make sure your controller is connected.")
        return

    print(f"Found {joystick_count} controller(s)")
    print("-" * 50)

    # Initialize the first joystick
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    print(f"Controller: {joystick.get_name()}")
    print(f"Buttons: {joystick.get_numbuttons()}")
    print(f"Axes: {joystick.get_numaxes()}")
    print(f"Hats: {joystick.get_numhats()}")
    print("-" * 50)
    print("\nPress buttons to see their numbers. Ctrl+C to quit.\n")

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    print(f"Button {event.button} pressed")
                elif event.type == pygame.JOYBUTTONUP:
                    print(f"Button {event.button} released")
                elif event.type == pygame.JOYAXISMOTION:
                    if abs(event.value) > 0.5:  # Threshold to avoid noise
                        print(f"Axis {event.axis}: {event.value:.2f}")
                elif event.type == pygame.JOYHATMOTION:
                    print(f"Hat {event.hat}: {event.value}")

    except KeyboardInterrupt:
        print("\n\nDone!")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
