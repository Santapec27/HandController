import pydirectinput
import pyautogui
import time
from config import Config

class InputEmitter:
    def __init__(self):
        self.is_mouse_down = False
        self.is_right_mouse_down = False
        self.is_middle_mouse_down = False
        self.scroll_start_y = None
        self.has_minimized = False
        
        self.left_pinch_start_time = None
        self.drag_locked = False
        
        pydirectinput.FAILSAFE = False
        pyautogui.FAILSAFE = False

    def emit(self, pos, is_clicking, is_right_clicking, is_middle_clicking, is_scrolling, is_minimizing):
        if pos is None:
            self._release_all()
            return

        x, y = pos
        # Constrain to screen size
        x = max(0, min(x, Config.SCREEN_WIDTH - 1))
        y = max(0, min(y, Config.SCREEN_HEIGHT - 1))
        
        # Scroll logic
        if is_scrolling:
            if self.scroll_start_y is None:
                self.scroll_start_y = y
            else:
                delta_y = self.scroll_start_y - y
                if abs(delta_y) > 10: # threshold for scroll 
                    # pyautogui scroll takes positive for up, negative for down
                    # in screen coords, Y goes down, so if hand moves up (Y decreases), delta_y is positive -> scroll up
                    scroll_amount = int(delta_y * 0.5) 
                    pyautogui.scroll(scroll_amount)
                    self.scroll_start_y = y
            # We skip moving the mouse pointer if we are scrolling
        else:
            self.scroll_start_y = None
            pydirectinput.moveTo(x, y)

        # Minimize logic (One-shot per gesture)
        if is_minimizing:
            if not self.has_minimized:
                pyautogui.hotkey('win', 'd')
                self.has_minimized = True
        else:
            self.has_minimized = False

        # Left click logic (Tap vs Drag)
        if is_clicking:
            if self.left_pinch_start_time is None:
                # Pinch just started
                self.left_pinch_start_time = time.time()
                self.drag_locked = False
            else:
                # Pinch is being held
                if not self.drag_locked and (time.time() - self.left_pinch_start_time) > Config.DRAG_DELAY:
                    # Time threshold reached, lock into drag mode
                    pydirectinput.mouseDown()
                    self.is_mouse_down = True
                    self.drag_locked = True
        else:
            if self.left_pinch_start_time is not None:
                # Pinch released
                if self.drag_locked:
                    # We were dragging, release the drag
                    pydirectinput.mouseUp()
                    self.is_mouse_down = False
                else:
                    # Quick tap! Emit a fast click
                    pydirectinput.click()
                
                self.left_pinch_start_time = None
                self.drag_locked = False
            
        # Right click logic
        if is_right_clicking and not self.is_right_mouse_down:
            pydirectinput.mouseDown(button='right')
            self.is_right_mouse_down = True
        elif not is_right_clicking and self.is_right_mouse_down:
            pydirectinput.mouseUp(button='right')
            self.is_right_mouse_down = False

        # Middle click logic
        if is_middle_clicking and not self.is_middle_mouse_down:
            pydirectinput.mouseDown(button='middle')
            self.is_middle_mouse_down = True
        elif not is_middle_clicking and self.is_middle_mouse_down:
            pydirectinput.mouseUp(button='middle')
            self.is_middle_mouse_down = False

    def _release_all(self):
        if self.is_mouse_down:
            pydirectinput.mouseUp()
            self.is_mouse_down = False
        if self.is_right_mouse_down:
            pydirectinput.mouseUp(button='right')
            self.is_right_mouse_down = False
        if self.is_middle_mouse_down:
            pydirectinput.mouseUp(button='middle')
            self.is_middle_mouse_down = False
        self.scroll_start_y = None
        self.has_minimized = False
        self.left_pinch_start_time = None
        self.drag_locked = False
