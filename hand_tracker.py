import cv2
import mediapipe as mp
import numpy as np
import math

class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Hand pose parameters
        self.hand_center = np.array([0.0, 0.0, 0.0])
        self.hand_rotation = np.eye(3)
        self.hand_translation = np.array([0.0, 0.0, 0.0])
        
        # Reference positions for pose calculation
        self.ref_wrist = None
        self.ref_middle_mcp = None
        self.ref_thumb_tip = None
        
    def get_hand_landmarks(self):
        """Capture frame and extract hand landmarks"""
        ret, frame = self.cap.read()
        if not ret:
            return None, None
            
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Draw landmarks on frame
            annotated_frame = frame.copy()
            self.mp_drawing.draw_landmarks(
                annotated_frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
            )
            
            return hand_landmarks, annotated_frame
        
        return None, frame
    
    def calculate_6dof_pose(self, landmarks):
        """Calculate 6DOF pose from hand landmarks"""
        if not landmarks:
            return None
            
        # Extract key landmark positions
        wrist = np.array([landmarks.landmark[0].x, landmarks.landmark[0].y, landmarks.landmark[0].z])
        middle_mcp = np.array([landmarks.landmark[9].x, landmarks.landmark[9].y, landmarks.landmark[9].z])
        thumb_tip = np.array([landmarks.landmark[4].x, landmarks.landmark[4].y, landmarks.landmark[4].z])
        index_tip = np.array([landmarks.landmark[8].x, landmarks.landmark[8].y, landmarks.landmark[8].z])
        
        # Calculate translation (hand center movement)
        hand_center = (wrist + middle_mcp) / 2
        
        # Normalize coordinates to [-1, 1] range
        translation = np.array([
            (hand_center[0] - 0.5) * 2.0,  # X: left-right
            (0.5 - hand_center[1]) * 2.0,  # Y: up-down (flipped)
            (hand_center[2] - 0.5) * 2.0   # Z: forward-backward
        ])
        
        # Calculate rotation using hand orientation
        # Vector from wrist to middle finger MCP
        forward_vector = middle_mcp - wrist
        forward_vector = forward_vector / np.linalg.norm(forward_vector)
        
        # Vector from wrist to thumb tip
        right_vector = thumb_tip - wrist
        right_vector = right_vector / np.linalg.norm(right_vector)
        
        # Cross product to get up vector
        up_vector = np.cross(forward_vector, right_vector)
        up_vector = up_vector / np.linalg.norm(up_vector)
        
        # Recalculate right vector to ensure orthogonality
        right_vector = np.cross(up_vector, forward_vector)
        right_vector = right_vector / np.linalg.norm(right_vector)
        
        # Create rotation matrix
        rotation_matrix = np.array([
            [right_vector[0], up_vector[0], forward_vector[0]],
            [right_vector[1], up_vector[1], forward_vector[1]],
            [right_vector[2], up_vector[2], forward_vector[2]]
        ])
        
        # Ensure proper rotation matrix
        U, _, Vt = np.linalg.svd(rotation_matrix)
        rotation_matrix = U @ Vt
        
        # Apply scaling for better control
        translation *= 0.5  # Scale down translation sensitivity
        
        return {
            'translation': translation,
            'rotation_matrix': rotation_matrix,
            'hand_center': hand_center,
            'confidence': 1.0
        }
    
    def get_pose_update(self):
        """Get the latest 6DOF pose update"""
        landmarks, frame = self.get_hand_landmarks()
        
        if landmarks:
            pose = self.calculate_6dof_pose(landmarks)
            return pose, frame
        
        return None, frame
    
    def cleanup(self):
        """Release camera resources"""
        self.cap.release()
        cv2.destroyAllWindows()