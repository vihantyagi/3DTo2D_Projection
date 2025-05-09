# 3D to 2D Wireframe Projection

A Python implementation for visualizing and interacting with 3D objects using 2D graphics.

## Overview

This project implements a 3D wireframe viewer that renders 3D objects as wireframes using only 2D graphics primitives. The application allows for interactive rotation of 3D objects using mouse controls, with object faces colored according to their orientation relative to the viewer.

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
python part2.py object.txt  # For colored face display
```

## Requirements

- Python 3.x
- NumPy
- Tkinter (usually comes with Python)

## Demo

![Wireframe Demo](wireframe_demo.gif)

## Development Notes

This project was developed as a technical assessment to demonstrate 3D graphics fundamentals without using dedicated 3D graphics libraries. It showcases understanding of:

- 3D to 2D projection algorithms
- Matrix transformations
- Interactive graphics
- Color interpolation based on viewing angle
- Face normal calculation

## Future Improvements

- Add support for more 3D file formats
- Implement Z-buffer algorithm for more accurate depth handling
- Add lighting effects and texture mapping
- Support for mesh subdivision and higher polygon counts

---

*Note: This project does not use any 3D graphics libraries or packages - all 3D mathematics and projections are implemented manually to demonstrate understanding of the underlying concepts.*
