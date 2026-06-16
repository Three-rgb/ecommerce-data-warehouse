# Week 1 任务清单:项目搭建 + 造数据

## 目标
- [ ] 跑通造数据脚本,生成 100 万订单
- [ ] 在 GitHub 建好仓库,完成首次提交
- [ ] 熟悉 Python 基础(pandas / Faker)

## 每天的具体任务

### Day 1(今天)- 环境准备
- [ ] 装 Python 3.8+(如未装)
- [ ] 装 VS Code 或 PyCharm
- [ ] `cd 01-data-generation && pip install -r ../requirements.txt`
- [ ] 跑 `python generate_users.py`,生成 10 万用户
- [ ] 跑 `python generate_products.py`,生成 5 千商品
- [ ] `git init && git add . && git commit -m "init: project skeleton"`

### Day 2 - 造订单数据
- [ ] 跑 `python generate_orders.py`,生成 100 万订单
- [ ] 看 `data/orders.csv` 字段,理解每列含义
- [ ] 尝试用 `pandas` 读 CSV,做 3 个简单统计:
  - 订单总量
  - 订单状态分布
  - 客单价

### Day 3 - 熟悉数据
- [ ] 用 pandas 做几个数据探索(EDA):
  - 各城市用户数 Top 10
  - 各品类销量 Top 10
  - 每月订单量趋势
- [ ] 把代码保存成 `01-data-generation/explore.py`

### Day 4 - ODS 层设计
- [ ] 学习 ODS 层是什么(原始数据接入)
- [ ] 创建 MySQL 数据库 `ecommerce_dw`
- [ ] 把 `data/users.csv`、`data/products.csv`、`data/orders.csv` 导入 MySQL
- [ ] 写一份 `02-ods-layer/README.md`,说明 ODS 层的设计

### Day 5 - DWD 层设计
- [ ] 学习 DWD 层(清洗明细层)
- [ ] 思考:订单数据需要做哪些清洗?
  - 去重
  - 空值处理
  - 数据类型转换
  - 异常值过滤(比如金额 < 0)

### Day 6 - 综合练习
- [ ] 用 SQL 写几个查询练手:
  - 查询每个用户首单时间
  - 查询复购用户(下过 2 单以上)
  - 查询每个品类的销售额 Top 3 商品

### Day 7 - 复盘 + 写周记
- [ ] 在 `docs/week1.md` 写下这周学到的:
  - 哪些会了
  - 哪些卡住
  - 下周要重点突破的

## 验收标准

跑完 `run_all.py` 后:
```bash
$ ls -lh data/
-rw-r--r-- 1 user user  12M  users.csv
-rw-r--r-- 1 user user 380K  products.csv
-rw-r--r-- 1 user user  95M  orders.csv
-rw-r--r-- 1 user user 240M  order_items.csv
```

如果出现这些文件,Week 1 完成 🎉

## 卡住了怎么办

- Faker 装不上:换镜像 `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple Faker`
- 生成太慢:把 `generate_orders.py` 里的 `N_ORDERS` 改成 10 万先跑通,再调大
- 跑出 OOM:分批生成,每次 10 万
- 其他问题:直接问我,把报错信息贴过来
