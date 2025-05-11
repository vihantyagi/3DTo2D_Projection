# 3D to 2D Wireframe Projection

A Python implementation for visualizing and interacting with 3D objects using 2D graphics.

## Overview

This project implements a 3D wireframe viewer that renders 3D objects as wireframes using only 2D graphics primitives. 

## Demo

https://github.com/user-attachments/assets/d61d55d3-9c55-4da9-8ae0-e210d33b376d
https://github.com/user-attachments/assets/bfce1421-7bb8-474b-82e2-d7d0e4925045



## Features

- **3D Object Parsing**: Reads 3D objects from comma-separated text files
- **Wireframe Visualization**: Displays objects as wireframes with vertices and edges
- **Interactive Rotation**: Click and drag to rotate objects
  - Horizontal movement rotates around Y-axis
  - Vertical movement rotates around X-axis
  - Diagonal movement combines both rotations
- **Normalized Scaling**: Objects are automatically scaled to fit optimally in the display window
- **Shaded Faces** (Part 2): Faces are colored based on their angle to the viewer
  - Color varies smoothly from #00005F (when viewed on edge) to #0000FF (when viewed flat)

## Technical Implementation

- **Pure 2D Graphics**: Implements 3D visualization using only 2D drawing primitives
- **Orthographic Projection**: Projects 3D coordinates onto a 2D plane assuming infinite viewer distance
- **Matrix-Based Rotation**: Uses rotation matrices to avoid gimbal lock
- **Face Normal Calculation**: Computes face normals to determine shading
- **Depth Sorting**: Correctly handles face overlap by rendering from back to front

## File Format

The application accepts 3D object files in the following format:
```
6,8
1,1.0,0.0,0.0
2,0.0,-1.0,0.0
3,0.0,0.0,1.0
...
1,2,3
1,2,6
...
```

Where:
- First line: `[number_of_vertices],[number_of_faces]`
- Vertex lines: `[vertex_id],[x],[y],[z]`
- Face lines: `[vertex_id1],[vertex_id2],[vertex_id3]`

## Usage

```bash
python part1.py object.txt  # For basic wireframe display
```

## Requirements

- Python 3.x
- NumPy
- Tkinter (usually comes with Python)
