# Airflow 安装指南(Windows)

## 1. 设置环境变量

打开 PowerShell,执行:

```powershell
# Airflow 安装目录
$env:AIRFLOW_HOME = "F:\DataEng\airflow_home"
[Environment]::SetEnvironmentVariable("AIRFLOW_HOME", "F:\DataEng\airflow_home", "User")

# 验证
echo $env:AIRFLOW_HOME
```

**重启 PowerShell 让环境变量生效。**

## 2. 装 Airflow

```powershell
# 激活 venv
F:\DataEng\venv\ecommerce\Scripts\Activate.ps1

# 设置镜像源(国内加速)
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 装 Apache Airflow
pip install "apache-airflow==2.8.0"
```

**这一步大约 3-5 分钟,会装几十个依赖包,耐心等。**

如果遇到 `Microsoft Visual C++ 14.0 is required` 错误:
- 装 Microsoft Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- 安装时勾选 "使用 C++ 的桌面开发"

## 3. 初始化数据库

```powershell
airflow db init
```

这会创建 SQLite 数据库,存储 DAG 状态、任务日志等。

## 4. 创建管理员账号

```powershell
airflow users create ^
    --username admin ^
    --firstname Admin ^
    --lastname User ^
    --role Admin ^
    --email admin@example.com ^
    --password admin
```

## 5. 启动 Airflow

**打开两个 PowerShell 窗口**(都激活 venv):

**窗口 1 - 启动 webserver:**
```powershell
airflow webserver --port 8080
```

**窗口 2 - 启动 scheduler:**
```powershell
airflow scheduler
```

## 6. 访问 Web UI

浏览器打开:http://localhost:8080

输入账号:`admin` / 密码:`admin`

应该看到 Airflow 的 DAG 列表页面。

## 7. 复制 dags 目录

把 `F:\Projects\ecommerce-data-warehouse\07-airflow-dag\dags\` 下的文件
**软链接或复制**到 Airflow 的 dags 目录:

```powershell
# 方法 1:软链接(推荐)
New-Item -ItemType Junction -Path "F:\DataEng\airflow_home\dags" -Target "F:\Projects\ecommerce-data-warehouse\07-airflow-dag\dags"

# 方法 2:复制
Copy-Item -Path "F:\Projects\ecommerce-data-warehouse\07-airflow-dag\dags\*" -Destination "F:\DataEng\airflow_home\dags" -Recurse
```

**重启 webserver 和 scheduler**,DAG 就会出现在 UI 上。

## 8. 触发第一个 DAG

UI 上点 "hello_world" DAG → 触发(Trigger DAG) → 看任务执行。

## 常见问题

**Q: 端口 8080 被占?**
```powershell
airflow webserver --port 8081
```

**Q: pip 装太慢?**
用清华镜像:上面已经配置了

**Q: airflow 命令找不到?**
检查 venv 是否激活,`which airflow` 应该指向 venv 里的

**Q: DAG 不显示?**
1. 检查 dags 文件是不是在 `F:\DataEng\airflow_home\dags\`
2. 重启 webserver 和 scheduler
3. 看 `F:\DataEng\airflow_home\logs\` 里的错误日志
