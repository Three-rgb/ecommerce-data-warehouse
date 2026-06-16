@echo off
chcp 65001 >nul
echo ============================================
echo   电商数仓项目 - F 盘环境初始化脚本
echo ============================================
echo.

:: 检查是否管理员
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 请右键用"以管理员身份运行"此脚本
    pause
    exit /b 1
)

echo [1/6] 创建 F 盘目录结构...
mkdir F:\Dev 2>nul
mkdir F:\Projects 2>nul
mkdir F:\DataEng 2>nul
mkdir F:\Workspace 2>nul
mkdir F:\DataEng\venv 2>nul
mkdir F:\DataEng\mysql_data 2>nul
mkdir F:\DataEng\hive_data 2>nul
mkdir F:\DataEng\spark_data 2>nul
mkdir F:\DataEng\airflow_home 2>nul
mkdir F:\Workspace\generated 2>nul
mkdir F:\DockerImages 2>nul
echo    [完成]
echo.

echo [2/6] 设置 pip 清华镜像(加速后续装包)...
set PIP_CONFIG_FILE=%USERPROFILE%\pip\pip.ini
if not exist "%USERPROFILE%\pip" mkdir "%USERPROFILE%\pip"
(
    echo [global]
    echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple
    echo trusted-host = pypi.tuna.tsinghua.edu.cn
) > "%USERPROFILE%\pip\pip.ini"
echo    [完成] 镜像源已配置
echo.

echo [3/6] 检查 Python...
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo    [警告] 未检测到 Python
    echo    请先安装 Python 到 F:\Dev\Python\
    echo    下载:https://www.python.org/downloads/
    echo    安装时勾选 "Add Python to PATH"
) else (
    echo    [完成] Python 已安装
    python --version
)
echo.

echo [4/6] 创建虚拟环境(F:\DataEng\venv\ecommerce)...
if exist F:\DataEng\venv\ecommerce (
    echo    [跳过] 虚拟环境已存在
) else (
    where python >nul 2>&1
    if %errorLevel% equ 0 (
        python -m venv F:\DataEng\venv\ecommerce
        if %errorLevel% equ 0 (
            echo    [完成] 虚拟环境已创建
        ) else (
            echo    [错误] 虚拟环境创建失败
        )
    )
)
echo.

echo [5/6] 设置系统环境变量...
setx DATA_OUTPUT_DIR "F:\Workspace\generated" >nul 2>&1
setx MYSQL_DATA_DIR "F:\DataEng\mysql_data" >nul 2>&1
echo    [完成] DATA_OUTPUT_DIR = F:\Workspace\generated
echo.

echo [6/6] 完成!
echo.
echo ============================================
echo   下一步操作
echo ============================================
echo.
echo 1. 把项目文件解压到 F:\Projects\ecommerce-data-warehouse\
echo 2. 激活虚拟环境: F:\DataEng\venv\ecommerce\Scripts\activate
echo 3. 装依赖: pip install -r F:\Projects\ecommerce-data-warehouse\requirements.txt
echo 4. 造数据: cd F:\Projects\ecommerce-data-warehouse\01-data-generation ^&^& python run_all.py
echo.
echo 数据会生成到 F:\Workspace\generated\
echo.
pause
