# Scan Controller

This project is a desktop application for controlling a 3D scanner. It provides a graphical user interface to manually move the scanner axes and configure its components.

## Features

-   Manual control of X, Y, and Z axes.
-   Real-time display of the scanner's current position.
-   Configuration panels for motion controller, probe, and other settings.

## Getting Started

### Prerequisites

-   Python 3.x
-   Git

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd scan-controller-main
    ```

2.  Install dependencies:
    This project uses PySide6 for its graphical user interface. As there is no `requirements.txt` file, you will need to install it manually:
    ```bash
    pip install PySide6
    ```

### Running the Application

To launch the scan controller GUI, run the `test_scanner_gui.py` script:

```bash
python test_scanner_gui.py
```

## Project Structure

-   `gui/`: Contains the Qt-based GUI code.
    -   `scanner_qt.py`: The main application window and logic.
    -   `ui_scanner.ui`: The user interface layout file created with Qt Designer.
    -   `ui_scanner.py`: The Python code generated from the `.ui` file.
-   `scanner/`: Contains the core scanner logic.
    -   `scanner.py`: The main scanner class.
    -   `motion_controller.py`: Handles the movement of the scanner.
    -   `probe_controller.py`: Manages the scanner's probe.
-   `test_scanner_gui.py`: The main entry point to run the application.

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a pull request.

## Testing

This project includes tests for the scanner command and GUI. To run the tests, execute the following files:

-   `test_scanner_command.py`: Tests the core scanner commands.
-   `test_scanner_gui.py`: Tests the graphical user interface.

```bash
python test_scanner_command.py
python test_scanner_gui.py
```
