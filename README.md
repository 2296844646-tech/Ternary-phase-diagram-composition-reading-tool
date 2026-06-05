# Ternary Phase Diagram Composition Reading Tool

A lightweight Python desktop tool for reading Ga-In-Sn ternary phase diagram compositions from an image.

The tool lets users load a ternary phase diagram, calibrate the three vertices in the order `Ga -> In -> Sn`, and click inside the triangle to estimate the corresponding composition using barycentric coordinates.

## Features

- Open local ternary phase diagram images.
- Calibrate triangle vertices interactively.
- Read Ga, In, and Sn composition percentages by clicking a point.
- Show whether the selected point is inside the triangle.
- Reset calibration and reuse the same image.
- Simple desktop UI built with Tkinter.

## Use Cases

This project is designed for materials science learning, alloy design notes, and quick composition estimation from ternary phase diagrams. It can help students and researchers reduce manual reading errors when working with Ga-In-Sn phase diagram images.

## Installation

Python 3.9 or later is recommended.

```bash
pip install -r requirements.txt
```

## Run

```bash
python ternary_reader.py
```

For compatibility with the original script name, this also works:

```bash
python 2.py
```

## How To Use

1. Start the program.
2. Click `打开图片` and select a ternary phase diagram image.
3. Click the three triangle vertices in this order: `Ga`, `In`, `Sn`.
4. After calibration, click any point in the triangle.
5. Read the Ga/In/Sn percentage values in the result area.

## Technical Notes

The composition is calculated with barycentric coordinates. After the three vertices are calibrated, each clicked point is transformed into three weights corresponding to `Ga`, `In`, and `Sn`. The weights are displayed as percentages and should sum to about `100 wt.%`.

## Project Status

This is an early-stage open source project. Planned improvements include:

- Add example phase diagram images.
- Add screenshots and a short usage demo.
- Add automated tests for barycentric coordinate calculation.
- Improve support for more ternary systems beyond Ga-In-Sn.
- Package the tool as a Windows executable for non-programming users.

## License

This project is released under the MIT License.
