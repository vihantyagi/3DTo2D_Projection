import tkinter as tk
import math
from itertools import combinations
import numpy as np
import sys

class ObjectDisplay:

    def __init__(self, root, object_path):
        
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

        # Add new variables for tracking closest vertex and mouse position
        self.closest_vertex = None
        self.center, self.centered_vertices = None, {} 
        self.center_vertices()
        
        # Bind mouse events for rotation
        self.canvas.bind("<ButtonPress-1>", self.mouse_click)
        self.canvas.bind("<B1-Motion>", self.calc_angle)

        # Draw the object initially
        self.draw_object()

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
        self.rotate_3d()  # Apply rotation to vertices
        
        # Project and draw the rotated verticesvertices
        projected_vertices = dict(map(lambda x: (x, self.project_3d_to_2d(self.vertices_c[x])), self.vertices_c))

        for vertex in self.vertices.keys():
            px, py = projected_vertices[vertex]
            # drawing oval on vertices
            self.canvas.create_oval(px-5, py+5, px+5, py-5, fill="blue")
                
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
        """Handle mouse drag for rotation"""
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

    def rotate_3d(self):
        """Apply the current rotation matrix to all vertices"""
        # Apply rotation to each vertex
        for vid, coords in self.centered_vertices.items():            

            # Apply the accumulated rotation matrix
            rotated_coords = self.rotation_matrix @ coords
            
            # Store the rotated coordinates (still centered)
            self.vertices_c[vid] = rotated_coords
    
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Display 3D object")
    filepath = sys.argv[1]
    tetrahedron_display = ObjectDisplay(root, filepath)
    root.mainloop()