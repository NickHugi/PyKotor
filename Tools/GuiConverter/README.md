# GUI Resizer CLI Tool

## Overview

This is a simple command-line interface (CLI) tool designed to adjust and scale GUI (Graphical User Interface) files based on different screen resolutions. The tool reads `.gui` files from the popular game Star Wars: Knights of the Old Republic and adjusts the layout to fit various resolutions and aspect ratios. It supports multiple resolutions and can handle batch processing of files.

## Features

- **Multi-Resolution Support**: The tool can adjust GUI files to fit several resolutions across different aspect ratios, such as 16:9, 16:10, 4:3, 5:4, 21:9, 3:2, and 1:1.
- **Batch Processing**: You can process multiple GUI files at once, making it easy to adjust a whole directory of files.
- **Logging**: Outputs logs to track the processing of files, including which resolutions were processed and where the output files are saved.
- **Cross-Platform**: Works on Windows, Linux, and macOS with Python 3.8+.

## Installation

To use this tool, you'll need to have Python 3.8 or higher installed on your system.

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install Dependencies**:
   Ensure you have the necessary Python packages installed. You may need to install `pykotor`, a package that handles `.gff` files, as well as any other dependencies.

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Command

To run the tool, use the following command:

```bash
python3 gui_resizer.py --input <input-path> --output <output-path> --resolution <resolution>
```

### Parameters

- **`--input`**: The path to the `.gui` file(s) you want to process. You can specify a single file or a directory containing multiple `.gui` files.
- **`--output`**: The directory where the processed files will be saved.
- **`--resolution`**: The target resolution(s). Use the format `WIDTHxHEIGHT` (e.g., `1920x1080`). You can also specify `ALL` to process all common resolutions.

### Example

To convert all `.gui` files in the directory `input_files/` to fit a 1920x1080 resolution and save them to the `output_files/` directory, run:

```bash
python3 gui_resizer.py --input input_files/ --output output_files/ --resolution 1920x1080
```

### Logging

If logging is enabled, a log file named `output.log` will be created in the specified output directory. This file will contain details of the processing operations performed.

## How It Works

1. **Input Handling**: The tool takes in `.gui` files or directories containing these files and reads them using the `pykotor` library.
  
2. **Resolution Scaling**: The tool scales the GUI elements based on the specified target resolution(s). It calculates scale factors based on the original dimensions of the GUI and applies these factors to resize elements accordingly.

3. **Output Generation**: The processed GUI files are then saved to the specified output directory, organized by resolution.

## Requirements

- **Python**: 3.8 or higher
- **OS**: Windows, Linux, or macOS
- **Dependencies**: Listed in `requirements.txt` (to be created based on the imports)

## Notes

- Ensure that your `.gui` files are compatible with the Star Wars: Knights of the Old Republic game or any other project you're working on.
- The tool supports adding more aspect ratios and resolutions by modifying the `ASPECT_RATIO_TO_RESOLUTION` dictionary in the script.
