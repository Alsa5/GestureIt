import warnings
import cv2
import mediapipe as mp
import pyautogui
import time
import os
import platform
import logging

# Set logging level to suppress warnings
logging.basicConfig(level=logging.ERROR)  # Adjust log level as needed


warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf')

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

previous_positions = []

last_gesture_time = time.time()
debounce_duration = 1  

def recognize_gesture(landmarks):
    global previous_positions
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]

    current_position = (index_tip.x, index_tip.y)
    previous_positions.append(current_position)
    if len(previous_positions) > 5:
        previous_positions.pop(0)
    if len(previous_positions) == 5:
        x_diff = previous_positions[-1][0] - previous_positions[0][0]
        y_diff = previous_positions[-1][1] - previous_positions[0][1]
        if abs(x_diff) > 2 * abs(y_diff): 
            if x_diff > 0.1:
                previous_positions = []
                return "previous"
            elif x_diff < -0.1:
                previous_positions = []
                return "next"
        elif abs(y_diff) > 2 * abs(x_diff): 
            if y_diff > 0.1:
                previous_positions = []
                return "volume_down"
            elif y_diff < -0.1:
                previous_positions = []
                return "volume_up"

    if (thumb_tip.y < index_tip.y and thumb_tip.y < middle_tip.y and
        thumb_tip.y < ring_tip.y and thumb_tip.y < pinky_tip.y):
        return "play_pause"

    if (index_tip.y < middle_tip.y and middle_tip.y < ring_tip.y and
        ring_tip.y < pinky_tip.y and thumb_tip.y < index_tip.y):
        return "volume_up"

    if (index_tip.y < middle_tip.y and middle_tip.y < ring_tip.y and
        ring_tip.y > pinky_tip.y and thumb_tip.y < index_tip.y and
        pinky_tip.y < thumb_tip.y):
        return "volume_down"

    return None

def get_active_window_title():
    if platform.system() == "Windows":
        import ctypes
        user32 = ctypes.windll.user32
        user32.GetForegroundWindow.restype = ctypes.wintypes.HWND
        user32.GetWindowTextLengthW.restype = ctypes.wintypes.INT
        user32.GetWindowTextW.restype = ctypes.wintypes.INT

        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    elif platform.system() == "Darwin":
        from AppKit import NSWorkspace
        return NSWorkspace.sharedWorkspace().frontmostApplication().localizedName()
    else:
        return None

def control_media_player(gesture):
    global last_gesture_time
    current_time = time.time()
    
    if current_time - last_gesture_time > debounce_duration or gesture in ["next", "previous"]:
        active_window = get_active_window_title()
        if "chrome" in active_window.lower() or "firefox" in active_window.lower():
            if gesture == "play_pause":
                pyautogui.press('k')
            elif gesture == "next":
                pyautogui.hotkey('shift', 'n') 
            elif gesture == "previous":
                pyautogui.hotkey('shift', 'p') 
            elif gesture == "volume_up":
                pyautogui.press('up')
            elif gesture == "volume_down":
                pyautogui.press('down') 
        else:
            if gesture == "play_pause":
                pyautogui.press('space')  
            elif gesture == "next":
                pyautogui.press('right')
            elif gesture == "previous":
                pyautogui.press('left')
            elif gesture == "volume_up":
                pyautogui.press('up')
            elif gesture == "volume_down":
                pyautogui.press('down')
        
        last_gesture_time = current_time

cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            gesture = recognize_gesture(hand_landmarks.landmark)
            if gesture:
                control_media_player(gesture)

    cv2.imshow("Hand Tracking", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
