# OSRS AI RL Manager GUI

This application provides a user-friendly Graphical User Interface (GUI) for managing the [OSRS PvP Reinforcement Learning project](https://github.com/Naton1/osrs-pvp-reinforcement-learning). It aims to simplify the process of setting up the environment, configuring training parameters, running training jobs, monitoring progress via TensorBoard, and managing bot credentials for the simulation server.

This GUI interacts with the scripts and configurations within the `pvp-ml` directory of the main project.

## Prerequisites

Before you begin, ensure you have the following software installed on your system:

1.  **Git:**
    *   Required for cloning the repository.
    *   You can download it from [git-scm.com](https://git-scm.com/).

2.  **Conda (Miniconda or Anaconda):**
    *   Required for managing the Python environment and dependencies for the AI model (`pvp-ml`). The GUI will help you set up this environment.
    *   Download Miniconda (recommended, lightweight) from [docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html) or Anaconda from [anaconda.com/products/distribution](https://anaconda.com/products/distribution).

3.  **Python (for the GUI):**
    *   Python 3.9 or newer is recommended for running the GUI itself. The AI model's Conda environment uses Python 3.10, which is also fine for the GUI.
    *   If you don't have a suitable Python version installed system-wide or via other means (like pyenv), you can download it from [python.org](https://www.python.org/downloads/).
    *   *Note: The GUI's dependencies (`PySide6`, `PyYAML`) will be installed into a separate Python virtual environment as described in the setup instructions below.*

## Setup Instructions

Follow these steps to set up and run the OSRS AI RL Manager GUI:

**Step 1: Clone the Repository**

1.  Open your terminal or command prompt.
2.  Clone the `osrs-pvp-reinforcement-learning` repository. If the GUI code is on a specific branch (e.g., `feature/gui-initial-build`), make sure to check out that branch.
    ```bash
    git clone https://github.com/Naton1/osrs-pvp-reinforcement-learning.git
    cd osrs-pvp-reinforcement-learning
    # Example: If the GUI is on a branch named 'feature/gui-initial-build', uncomment and run:
    # git checkout feature/gui-initial-build
    ```
    *Note: For these instructions, we'll assume you are in the root directory of this cloned repository.*

**Step 2: Set Up Python Environment for the GUI**

This GUI application runs in its own Python environment, separate from the Conda environment used by the AI model.

1.  Navigate to the GUI's directory:
    ```bash
    cd osrs_rl_gui
    ```
    *(If you're not already in the `osrs-pvp-reinforcement-learning` root, adjust your path accordingly to find the `osrs_rl_gui` subdirectory).*

2.  Create a Python virtual environment. This helps manage dependencies locally.
    ```bash
    python -m venv .gui_env
    ```
    *(You can name `.gui_env` whatever you prefer, e.g., `venv`)*

3.  Activate the virtual environment:
    *   On Windows:
        ```bash
        .gui_env\Scripts\activate
        ```
    *   On macOS and Linux:
        ```bash
        source .gui_env/bin/activate
        ```
    You should see the environment name (e.g., `(.gui_env)`) prefixed to your terminal prompt.

4.  Install the GUI's dependencies:
    ```bash
    pip install -r requirements.txt
    ```

**Step 3: Initial Configuration via the GUI**

1.  Launch the GUI application:
    Make sure your virtual environment from Step 2.3 is still active. From within the `osrs_rl_gui` directory:
    ```bash
    python main.py
    ```

2.  Configure the AI Model Project Path:
    *   Once the GUI opens, go to the **"Setup"** tab.
    *   In the "OSRS PvP RL Repo Path" field, click **"Browse..."** and navigate to and select the root directory of your cloned `osrs-pvp-reinforcement-learning` repository (the one you cloned in Step 1). This path will be saved for future sessions.

3.  Set Up the AI Model's Conda Environment:
    *   Still in the **"Setup"** tab:
        *   Verify that "Conda status" indicates Conda has been detected. If not, ensure Conda is installed and in your system's PATH.
        *   Choose whether you want to "Use CPU only for training" by checking/unchecking the box.
        *   Click the **"Setup Conda Environment"** button.
        *   The GUI will attempt to create (or verify) the necessary Conda environment (named `env`) inside the `pvp-ml` directory of your selected repository. You'll see live output in the feedback area. This step may take some time as it downloads and installs all the AI model's dependencies.
    *   Once successfully completed, the "Conda status" label should update to reflect the environment's creation.

You are now ready to use the other features of the GUI.

## Running the GUI

Once you have completed the initial setup:

1.  Open your terminal or command prompt.
2.  Navigate to the GUI's directory (e.g., `path/to/your/cloned/repo/osrs-pvp-reinforcement-learning/osrs_rl_gui`).
3.  Activate the Python virtual environment you created during setup:
    *   On Windows:
        ```bash
        .gui_env\Scripts\activate
        ```
    *   On macOS and Linux:
        ```bash
        source .gui_env/bin/activate
        ```
4.  Run the main application script:
    ```bash
    python main.py
    ```
This will launch the OSRS AI RL Manager GUI.

## Basic Usage Overview

Once the GUI is running and configured, you can use its various tabs to manage your OSRS AI RL project:

*   **Setup Tab:**
    *   Verify or change the path to your `osrs-pvp-reinforcement-learning` project.
    *   Manage the AI model's Conda environment (e.g., recreate if needed, switch between CPU/GPU if supported by your modifications to the environment file).

*   **Training Tab:**
    *   **Configuration Profile:** Select a YAML configuration file from the `pvp-ml/config` directory. The parameters will be displayed in a tree view.
    *   **Edit Configuration:** Modify simple parameter values (strings, numbers, booleans) directly in the tree.
    *   **Save Configuration:** Use "Save Configuration" to overwrite the selected profile or "Save Configuration As..." to create a new profile with your changes.
    *   **Training Execution:**
        *   Enter an "Experiment Name."
        *   Click "Start Training" to begin a training run using the selected profile and experiment name. Live logs from the training script will appear in the text area below.
        *   Click "Stop Training (Cleanup)" to terminate the current training process and run the `train cleanup` command for the experiment.
        *   Click "Launch TensorBoard" to start TensorBoard and monitor training progress (usually opens automatically in your browser at `http://localhost:6006`).

*   **Bot Credentials Tab:**
    *   Enter and save the OSRS username and password that your AI bot will use to log into the game on the simulation server.
    *   *(Remember the current warning: these are saved in plain text via QSettings for now. Secure storage is planned).*

*   **Monitoring / Admin Tabs:**
    *   These are currently placeholders for future functionality.

Refer to the tooltips within the application for more specific guidance on individual fields and buttons.

---

*This README is specifically for the GUI application. For information on the AI model itself, please refer to the main project README or the `pvp-ml` directory README.*
