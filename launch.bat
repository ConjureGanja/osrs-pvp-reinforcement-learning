@echo off
REM OSRS PvP RL - Quick Launcher (Windows)

set PROJECT_ROOT=%~dp0
set CONDA_ENV_PATH=%PROJECT_ROOT%pvp-ml\env

echo 🗡️ OSRS PvP Reinforcement Learning - Launcher
echo ==============================================
echo.

echo Available commands:
echo   1. setup         - Run automated setup
echo   2. gui           - Launch web GUI interface
echo   3. train         - Start training (requires preset)
echo   4. eval          - Evaluate model
echo   5. serve-api     - Serve models via API
echo   6. tensorboard   - View training progress
echo   7. simulation    - Start simulation server
echo.

if "%1"=="setup" (
    echo Running automated setup...
    python "%PROJECT_ROOT%setup.py" %2 %3 %4 %5 %6 %7 %8 %9
) else if "%1"=="gui" (
    echo Launching web GUI...
    python "%PROJECT_ROOT%web_gui.py" %2 %3 %4 %5 %6 %7 %8 %9
) else if "%1"=="train" (
    echo Starting training...
    if exist "%CONDA_ENV_PATH%" (
        conda run -p "%CONDA_ENV_PATH%" train %2 %3 %4 %5 %6 %7 %8 %9
    ) else (
        echo ❌ Conda environment not found. Run 'launch.bat setup' first.
    )
) else if "%1"=="eval" (
    echo Starting evaluation...
    if exist "%CONDA_ENV_PATH%" (
        conda run -p "%CONDA_ENV_PATH%" eval %2 %3 %4 %5 %6 %7 %8 %9
    ) else (
        echo ❌ Conda environment not found. Run 'launch.bat setup' first.
    )
) else if "%1"=="serve-api" (
    echo Starting API server...
    if exist "%CONDA_ENV_PATH%" (
        conda run -p "%CONDA_ENV_PATH%" serve-api %2 %3 %4 %5 %6 %7 %8 %9
    ) else (
        echo ❌ Conda environment not found. Run 'launch.bat setup' first.
    )
) else if "%1"=="tensorboard" (
    echo Starting Tensorboard...
    if exist "%CONDA_ENV_PATH%" (
        conda run -p "%CONDA_ENV_PATH%" train tensorboard
    ) else (
        echo ❌ Conda environment not found. Run 'launch.bat setup' first.
    )
) else if "%1"=="simulation" (
    echo Starting simulation server...
    cd /d "%PROJECT_ROOT%simulation-rsps\ElvargServer"
    if exist "gradlew.bat" (
        gradlew.bat run
    ) else (
        echo ❌ Gradle wrapper not found in simulation directory.
    )
) else (
    echo Usage: launch.bat ^<command^> [arguments...]
    echo.
    echo Quick Start:
    echo   launch.bat setup     # First-time setup
    echo   launch.bat gui       # Launch web interface
    echo.
    echo See SETUP_GUIDE.md for detailed instructions.
)