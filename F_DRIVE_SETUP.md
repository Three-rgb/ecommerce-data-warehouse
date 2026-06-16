# F 盘环境搭建指南

## 一次性目录规划

打开 PowerShell(管理员)或 CMD,执行下面的命令创建目录:

```cmd
mkdir F:\Dev
mkdir F:\Projects
mkdir F:\DataEng
mkdir F:\Workspace
mkdir F:\DataEng\venv
mkdir F:\DataEng\mysql_data
mkdir F:\DataEng\hive_data
mkdir F:\DataEng\spark_data
mkdir F:\Workspace\generated
```

## 装机时的建议

### 1. Python
- 装到 `F:\Dev\Python\Python311\`(自定义安装,不要放 C 盘)
- 勾选 "Add Python to PATH"
- pip 装好后立刻换源:
  ```cmd
  pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
  ```

### 2. VSCode
- 装到 `F:\Dev\VSCode\`
- 第一次打开时,把工作区指向 `F:\Projects`

### 3. MySQL
- 装到 `F:\Dev\MySQL\`
- 数据目录指向 `F:\DataEng\mysql_data`
- 配置时把字符集选 `utf8mb4`

## 项目放在 F 盘

把下载的 `ecommerce-data-warehouse.tar.gz` 解压到:
```
F:\Projects\ecommerce-data-warehouse\
```

## 虚拟环境(很重要!)

**不要在 C 盘建虚拟环境**,在 F 盘建:

```cmd
cd /d F:\Projects\ecommerce-data-warehouse
F:\Dev\Python\Python311\python.exe -m venv F:\DataEng\venv\ecommerce

# 激活虚拟环境
F:\DataEng\venv\ecommerce\Scripts\activate.bat

# 装依赖(现在装到 F 盘,不会占 C 盘)
pip install -r requirements.txt
```

## 数据生成放 F 盘

把生成的数据放到 `F:\Workspace\generated\`,不要放在项目目录里(避免污染代码库)。

修改 `01-data-generation/` 下所有脚本里的输出路径,把:
```python
OUTPUT_DIR = Path(__file__).parent.parent / "data"
```

改成:
```python
OUTPUT_DIR = Path("F:/Workspace/generated")
```

或者用环境变量(推荐):
```python
import os
OUTPUT_DIR = Path(os.environ.get("DATA_OUTPUT_DIR", Path(__file__).parent.parent / "data"))
```

然后运行前:
```cmd
set DATA_OUTPUT_DIR=F:\Workspace\generated
python run_all.py
```

## IDE 工作区

VSCode 打开 `F:\Projects\ecommerce-data-warehouse\`,然后 `File -> Save Workspace As` 保存为 `F:\Projects\ecommerce-dw.code-workspace`,以后直接双击这个文件进入项目。

## 后续工具的安装位置

| 工具 | 装到 F 盘哪里 | 数据目录 |
|------|--------------|----------|
| MySQL | F:\Dev\MySQL | F:\DataEng\mysql_data |
| Hive | F:\Dev\Hive | F:\DataEng\hive_data |
| Spark | F:\Dev\Spark | F:\DataEng\spark_data |
| Airflow | pip 装在 venv 里 | F:\DataEng\airflow_home |
| Docker Desktop | C 盘(系统工具,无法避免) | 镜像存 F:\DockerImages |

## 一键初始化脚本

我帮你写了一个 `setup_f_drive.bat`,管理员运行后会自动建好所有目录。

## 注意事项

1. **虚拟环境别每个项目一个** — 在 `F:\DataEng\venv\` 下建一个共享的 `ecommerce` 就行,所有数据项目复用
2. **MySQL 的 data 目录一定要改** — 不然默认放 C 盘,几天就满
3. **Docker Desktop 没法完全移 F 盘** — 但可以配置镜像存 F 盘,详见 Docker 文档
4. **不要把数据 CSV 提交到 Git** — `.gitignore` 已经配好,放 `F:\Workspace\generated\` 完全在外面,不会污染
