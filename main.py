import tkinter as tk
import math
from itertools import combinations
import itertools
import numpy as np
import sys
import csv
import threading
import time

# Try to import hand tracking (optional)
try:
    from hand_tracker import HandTracker
    HAND_TRACKING_AVAILABLE = True
except ImportError:
    HAND_TRACKING_AVAILABLE = False
    print("Hand tracking not available. Install opencv-python and mediapipe for camera support.") 

class ObjectDisplay:

    def __init__(self, root, object_path, control_mode=1):
        
        # percieved distance of object from viewer. 
        self.d = 10 
        self.vertices, self.edges = {}, []
        self.dx, self.dy, self.dz = 0, 0, 0
        self.k = 0.005
        
        # Read vertices and edges from file
        with open(object_path, 'r') as file:
            lines = file.readlines()        
        
        num_vertices, num_edges = int(lines[0].split(',')[0]), int(lines[0].split(',')[1])
        
        for i in range(1, num_vertices+1):
            v, x, y, z = lines[i].strip().split(',')
            # Convert coordinates to numpy array
            self.vertices[int(v)] = np.array([float(x), float(y), float(z)])
        self.assign_colour()

        # Copy vertices for transformations
        self.vertices_c = {k: v.copy() for k, v in self.vertices.items()}
        
        for i in range(num_vertices + 1, num_vertices + num_edges + 1):
            v1, v2, v3 = lines[i].strip().split(',')
            self.edges.append((int(v1), int(v2), int(v3)))

        # self.window_size = self.calculate_max_distance()

        # if self.window_size < 500: self.window_size = 500
        self.window_size = 1000
        self.canvas = tk.Canvas(root, width=self.window_size, height=self.window_size, bg="white")
        self.canvas.pack()

        # Initialize variables for rotation
        self.previous_x, self.previous_y = 0, 0 
        
        # Store rotation as a matrix instead of angles to avoid gimbal lock
        self.rotation_matrix = np.identity(3)  
        
        # Control mode: 0 = camera, 1 = mouse
        self.control_mode = control_mode
        
        # Hand tracking variables
        self.hand_tracker = None
        self.hand_tracking_enabled = False
        self.current_pose = None
        self.tracking_thread = None
        self.running = True
        
        # Add new variables for tracking closest vertex and mouse position
        self.closest_vertex = None
        self.center, self.centered_vertices = None, {} 
        self.center_vertices()
        
        # Initialize control mode first
        self.setup_control_mode()
        
        # Create control panel after control mode is set
        self.create_control_panel(root)
        
        # Draw the object initially
        self.draw_object()
        
        # Start update loop if using hand tracking (after mode is finalized)
        if self.control_mode == 0 and self.hand_tracking_enabled:
            self.update_loop()

    def assign_colour(self):
        """
        Assign each vertex a distinct color so you can follow the movements more clearly as you rotate it. 
        """
        with open('colors.csv', newline='') as csvfile:
            reader = csv.reader(csvfile)
            color_list = next(reader)

        self.vertex_colors = {
            vid: color
            for vid, color in zip(
                self.vertices.keys(),
                itertools.cycle(color_list)
            )
        }


    def center_vertices(self):
        """
        Calculate the center of the object based on vertex positions.
        """
        if not self.vertices:
            self.center = np.array([0.0, 0.0, 0.0])
            return
            
        # Calculate the average position of all vertices
        sum_pos = np.zeros(3)
        for vertex in self.vertices.values():
            sum_pos += vertex
            
        self.center = sum_pos / len(self.vertices)
        print(f"Object center: {self.center}")

        self.centered_vertices = {k: v - self.center for k, v in self.vertices.items()}
        
    def create_control_panel(self, root):
        """Create control panel for display options"""
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10)
        
        # Control mode display
        mode_text = "Camera Control" if self.control_mode == 0 else "Mouse Control"
        tk.Label(control_frame, text=f"Mode: {mode_text}", 
                font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10)
        
        # Reset button
        tk.Button(control_frame, text="Reset Pose", 
                 command=self.reset_pose).pack(side=tk.LEFT, padx=5)
        
        # Sensitivity slider (only for camera mode)
        if self.control_mode == 0:
            tk.Label(control_frame, text="Sensitivity:").pack(side=tk.LEFT, padx=5)
            self.sensitivity_var = tk.DoubleVar(value=1.0)
            tk.Scale(control_frame, from_=0.1, to=3.0, resolution=0.1, 
                    orient=tk.HORIZONTAL, variable=self.sensitivity_var).pack(side=tk.LEFT, padx=5)
            
            # Hand tracking status
            self.status_label = tk.Label(control_frame, text="Initializing...", fg="blue")
            self.status_label.pack(side=tk.LEFT, padx=10)
    
    def setup_control_mode(self):
        """Setup the appropriate control mode"""
        if self.control_mode == 0:  # Camera control
            print("TEST 1 - CONTROL MODE 0 - CAMERA")
            if HAND_TRACKING_AVAILABLE:
                self.hand_tracking_enabled = True
                self.start_hand_tracking()
            else:
                print("Hand tracking not available. Falling back to mouse control.")
                self.control_mode = 1
                self.setup_mouse_control()
        else:  # Mouse control
            print("TEST 1 - CONTROL MODE 1 - MOUSE")
            self.setup_mouse_control()
    
    def setup_mouse_control(self):
        """Setup mouse control bindings"""
        print("TEST 2 - CONTROL MODE 1 - MOUSE")
        self.canvas.bind("<ButtonPress-1>", self.mouse_click)
        self.canvas.bind("<B1-Motion>", self.calc_angle)
    
    def start_hand_tracking(self):
        """Start hand tracking in a separate thread"""
        print("TEST 2 - CONTROL MODE 0 - CAMERA")
        if self.tracking_thread is None or not self.tracking_thread.is_alive():
            self.tracking_thread = threading.Thread(target=self.hand_tracking_loop, daemon=True)
            self.tracking_thread.start()
    
    def hand_tracking_loop(self):
        """Main hand tracking loop running in separate thread"""
        try:
            self.hand_tracker = HandTracker()
            self.update_status("Hand tracking active")
        except Exception as e:
            self.update_status(f"Hand tracking failed: {str(e)}")
            return
            
        while self.running and self.hand_tracking_enabled:
            try:
                pose, frame = self.hand_tracker.get_pose_update()
                
                if pose:
                    self.current_pose = pose
                    self.update_status("Hand detected")
                else:
                    self.update_status("No hand detected")
                
                # Show camera feed
                if frame is not None:
                    import cv2
                    cv2.imshow('Hand Tracking - Press q to close', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.running = False
                        break
                        
            except Exception as e:
                print(f"Hand tracking error: {e}")
                time.sleep(0.1)
    
    def update_status(self, message):
        """Update status label safely from thread"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
    
    def update_loop(self):
        """Main update loop for camera mode"""
        if self.running:
            self.draw_object()
            self.canvas.after(30, self.update_loop)  # Update at ~30 FPS
    
    def reset_pose(self):
        """Reset pose to original position"""
        self.rotation_matrix = np.identity(3)
        self.current_pose = None
        if self.control_mode == 0:
            self.draw_object()
        else:
            self.draw_object() 

    def project_3d_to_2d(self, coords):
        """ project the 3d coordinates to 2d plane"""
        
        # Add center back to get the original coordinates
        original = coords + self.center
        x, y, z = original[0], original[1], original[2] 
        
        # Parallel projection for infinite distance observer
        x1 = x
        y1 = -y  # Flip y-axis to match Tkinter's coordinate system (top to bottom)

        # # Find the maximum extent of the object
        max_x = max(abs(v[0]) for v in self.centered_vertices.values())
        max_y = max(abs(v[1]) for v in self.centered_vertices.values())

        # Normalize coordinates to [-1, 1]
        a = max(max_x, max_y)
        x1 = x1 / a
        y1 = y1 / a
        
        # Center the coordinates in the window
        x1 = x1 * self.window_size/4 + self.window_size / 2
        y1 = y1 * self.window_size/4 + self.window_size / 2
        
        return int(x1), int(y1)  

    def draw_object(self):
        """ draw the 2d projection of the 3d object """

        self.canvas.delete("all")
        self.apply_transforms()  # Apply appropriate transforms based on control mode
        
        # Project and draw the transformed vertices
        projected_vertices = dict(map(lambda x: (x, self.project_3d_to_2d(self.vertices_c[x])), self.vertices_c))

        for vertex in self.vertices.keys():
            px, py = projected_vertices[vertex]
            # drawing oval on vertices
            self.canvas.create_oval(px-10, py+10, px+10, py-10, fill=self.vertex_colors[vertex])
                
        for edge in self.edges:
            combinations_of_2 = list(combinations(edge, 2))
            for i in combinations_of_2:
                start, end = i
                x1, y1 = projected_vertices[start]
                x2, y2 = projected_vertices[end]
                # drawing the edges. 
                self.canvas.create_line(x1, y1, x2, y2, fill="blue", width=3)

    def mouse_click(self, e):
        """Handle mouse click event"""
        self.previous_x, self.previous_y = e.x, e.y
    
    def rotation_matrix_x(self, angle):
        """Create rotation matrix for X-axis rotation"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return np.array([
            [1, 0, 0],
            [0, cos_a, -sin_a],
            [0, sin_a, cos_a]
        ])
    
    def rotation_matrix_y(self, angle):
        """Create rotation matrix for Y-axis rotation"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return np.array([
            [cos_a, 0, sin_a],
            [0, 1, 0],
            [-sin_a, 0, cos_a]
        ])

    def calc_angle(self, e):
        """Handle mouse drag for rotation (mouse mode only)"""
        if self.control_mode == 0:  # Skip if in camera mode
            return
            
        # Calculate mouse movement
        dx = e.x - self.previous_x
        dy = e.y - self.previous_y
        
        # Skip if there's no movement
        if dx == 0 and dy == 0:
            return
            
        # Sensitivity factor for rotation
        sensitivity = 0.01
        
        # Create rotation matrices for the incremental rotations
        # For Y movement, rotate around X axis
        if dy != 0:
            angle_x = dy * sensitivity
            rotation_x = self.rotation_matrix_x(angle_x)
            # Apply to the accumulated rotation matrix
            self.rotation_matrix = rotation_x @ self.rotation_matrix
            
        # For X movement, rotate around Y axis
        if dx != 0:
            angle_y = dx * sensitivity
            rotation_y = self.rotation_matrix_y(angle_y)
            # Apply to the accumulated rotation matrix
            self.rotation_matrix = rotation_y @ self.rotation_matrix
        
        # Update previous mouse position
        self.previous_x, self.previous_y = e.x, e.y
        
        # Redraw with new orientation
        self.draw_object()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.hand_tracker:
            self.hand_tracker.cleanup()
        try:
            import cv2
            cv2.destroyAllWindows()
        except:
            pass

    def apply_transforms(self):
        """Apply transforms based on control mode"""
        for vid, coords in self.centered_vertices.items():
            # Start with the original centered coordinates
            transformed_coords = coords.copy()
            
            # Apply hand tracking transforms if in camera mode
            if self.control_mode == 0 and self.hand_tracking_enabled and self.current_pose:
                # Apply hand tracking rotation
                hand_rotation = self.current_pose['rotation_matrix']
                transformed_coords = hand_rotation @ transformed_coords
                
                # Apply hand tracking translation
                hand_translation = self.current_pose['translation']
                if hasattr(self, 'sensitivity_var'):
                    transformed_coords += hand_translation * self.sensitivity_var.get()
                else:
                    transformed_coords += hand_translation
            
            # Apply manual rotation (for mouse mode or additional rotation)
            transformed_coords = self.rotation_matrix @ transformed_coords
            
            # Store the transformed coordinates
            self.vertices_c[vid] = transformed_coords
    
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <object_file> <control_mode>")
        print("  object_file: Path to the 3D object file")
        print("  control_mode: 0 for camera (hand tracking), 1 for mouse")
        print("Example: python main.py objects/object1.txt 0")
        sys.exit(1)
    
    filepath = sys.argv[1]
    control_mode = int(sys.argv[2])
    
    if control_mode not in [0, 1]:
        print("Error: control_mode must be 0 (camera) or 1 (mouse)")
        sys.exit(1)
    
    root = tk.Tk()
    mode_title = "Camera Control" if control_mode == 0 else "Mouse Control"
    root.title(f"3D Object Display - {mode_title}")
    
    display = ObjectDisplay(root, filepath, control_mode)
    
    def on_closing():
        display.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()