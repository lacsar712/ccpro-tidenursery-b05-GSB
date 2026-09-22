# TideNursery-01 · 潮汐育苗台账

海水育苗场「塘口水质采样与投喂事件」台账种子项目（非库存 / 电商 / 医院）。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.11 · FastAPI · SQLAlchemy 2 · Pydantic v2 · python-jose · passlib(bcrypt) · uvicorn |
| 前端 | React 18 · Vite · TypeScript · React Router v6 |
| 数据库 | PostgreSQL 15 |
| 部署 | docker-compose · 前端 Nginx 反代 `/api` |

## 端口与账号

| 服务 | 端口 |
| --- | --- |
| 前端 | **3400** |
| 后端 API | **8400** |
| PostgreSQL | **5434** |

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `123456` | 场长 |
| `technician` | `123456` | 水质技术员 |

## 一键启动

```bash
cd TideNursery-01
docker compose up --build
```

启动后访问：

- 前端：http://localhost:3400
- 后端健康检查：http://localhost:8400/api/health
- API 文档：http://localhost:8400/docs

后端 entrypoint 流程：等待数据库就绪 → `create_all` 建表 → seed 初始数据 → 启动 uvicorn。

## 功能模块

1. **Auth**：JWT 登录（OAuth2 Password），`/api/auth/login`、`/api/auth/me`
2. **Hatchery 育苗场**：`name`、`seawaterSource`、`notes`；海水源字段不能经普通 PUT 修改，只能走海水源切换登记
3. **Pond 育苗塘**：`hatcheryId`、`pondCode`、`species`、`volumeM3`、`status(stocked|dry|quarantine)`；同场 `pondCode` 唯一
4. **WaterSample 水质样**：`pondId`、`sampledAt`、`tempC`、`salinityPpt`、`doMgL`、`ph`、`notes`；`doMgL > 0` 且 `ph ∈ [6,9]`，否则返回 **400**；支持 POST 新建与 PUT 更新
5. **FeedEvent 投喂**：`pondId`、`fedAt`、`feedType`、`amountKg`、`operatorName`
6. **Dashboard**：塘总数、quarantine 数、近 24h 采样数、近 7 日投喂总量 kg

## 海水源切换日志与 24 小时水源确认

育苗场海水源变更**必须登记切换日志**，禁止只改场字段不写日志，也禁止只写日志不改场字段：

- `POST /api/hatcheries/{id}/source-switches`（场页「海水源切换登记」）同事务完成两件事：
  写入一条切换日志，并把育苗场 `seawaterSource` 更新为新水源摘要。
- 日志字段：所属育苗场、切换时刻、旧水源摘要、新水源摘要、操作人。
  新水源摘要去空白后**至少 4 个字**，否则 **400**。
- 查询：`GET /api/hatcheries/{id}/source-switches`（单场日志）、
  `GET /api/source-switches`（全部日志）。

**确认规则**：自切换时刻起 **24 小时**内（水源确认窗），该场下属塘口新建或更新水质样，
请求必须携带 `sourceConfirmation`，且其去空白后与该场最近一次切换的新水源摘要去空白后
**完全相同**；缺失或不一致一律返回 **409**（更新已有样缺失确认同样拒绝）。超过 24 小时
不再要求确认。

- 场列表/单场响应每行带 `sourceConfirmationOpen`（是否处于水源确认窗）；
- `GET /api/hatcheries/source-confirmations/open-count` 返回开放确认窗的场数
  （`openCount`），与场列表各行标记口径一致。

种子数据中「东港潮汐一号场」刚切换 2 小时（近海沙滤井水 → 外海深管抽海水），仍处于确认窗内。

## 前端页面

Login · Dashboard · Hatcheries · Ponds · WaterSamples · FeedEvents

## 本地开发（可选）

```bash
# 数据库（或用 compose 只起 db）
docker compose up -d db

# 后端
cd backend
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg2://tidenursery:tidenursery@localhost:5434/tidenursery
python -c "from app.database import Base, engine; from app import models; Base.metadata.create_all(bind=engine)"
python -c "from app.seed import seed; seed()"
uvicorn app.main:app --reload --port 8400

# 前端
cd frontend
npm install
npm run dev
```

## 目录结构

```
TideNursery-01/
├── docker-compose.yml
├── README.md
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── auth.py
│       ├── seed.py
│       ├── models/
│       ├── schemas/
│       └── routers/
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── pages/
        ├── components/
        └── api/
```
