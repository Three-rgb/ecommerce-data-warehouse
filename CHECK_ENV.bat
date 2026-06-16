@echo off
:: ============================================
:: Environment Diagnostic Script
:: Run this and send me the output
:: ============================================

echo === Environment Diagnostic ===
echo.

echo [1] Working directory:
cd
echo.

echo [2] Python info:
where python 2>nul
python --version 2>nul
echo.

echo [3] pip info:
where pip 2>nul
pip --version 2>nul
echo.

echo [4] Project directory check:
if exist "F:\Projects\ecommerce-data-warehouse" (
    echo       F:\Projects\ecommerce-data-warehouse EXISTS
    echo.
    echo       Contents:
    dir "F:\Projects\ecommerce-data-warehouse" /B
) else (
    echo       F:\Projects\ecommerce-data-warehouse NOT FOUND
    echo.
    echo       F:\Projects contents:
    if exist "F:\Projects" (
        dir "F:\Projects" /B
    ) else (
        echo       F:\Projects does not exist
    )
)
echo.

echo [5] requirements.txt check:
if exist "F:\Projects\ecommerce-data-warehouse\requirements.txt" (
    echo       Found! Size:
    dir "F:\Projects\ecommerce-data-warehouse\requirements.txt"
) else (
    echo       NOT found
)
echo.

echo [6] Virtual environment check:
if exist "F:\DataEng\venv\ecommerce\Scripts\python.exe" (
    echo       Virtual env EXISTS at F:\DataEng\venv\ecommerce\
) else (
    echo       Virtual env NOT FOUND
)
echo.

echo [7] Output directory check:
if exist "F:\Workspace\generated" (
    echo       F:\Workspace\generated EXISTS
) else (
    echo       F:\Workspace\generated NOT FOUND
)
echo.

echo [8] F: drive space:
wmic logicaldisk where "DeviceID='F:'" get FreeSpace,Size /format:list 2>nul
echo.

echo === Diagnostic Complete ===
echo Please send the full output to your assistant.
pause
