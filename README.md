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
2. **Hatchery 育苗场**：`name`、`seawaterSource`、`notes`；列表每行带 `sourceConfirmationOpen`（是否处于水源确认窗），`GET /api/hatcheries/source-confirmation-open-count` 返回开放确认窗场数，二者口径一致
3. **海水源切换日志**：海水源变更必须登记切换，禁止只改场字段不写日志、也禁止只写日志不改场字段。`POST /api/hatcheries/{id}/source-switches` 在**同一事务**内写日志并更新场上海水源字段。日志字段：所属育苗场、切换时刻、旧水源摘要、新水源摘要（去空白至少 4 字）、操作人；`GET /api/hatcheries/{id}/source-switches` 查询该场切换记录
4. **水源确认规则**：自切换时刻起 **24 小时内**，该场下属塘口**新建或更新**水质样，请求必须带 `sourceConfirmation`，且其去空白后与新水源摘要相同，否则返回 **409**；改已有样缺确认同样拒绝。超过 24 小时不再要求确认。海水源字段不可通过普通的育苗场 PUT 接口直接修改
5. **Pond 育苗塘**：`hatcheryId`、`pondCode`、`species`、`volumeM3`、`status(stocked|dry|quarantine)`；同场 `pondCode` 唯一
6. **WaterSample 水质样**：`pondId`、`sampledAt`、`tempC`、`salinityPpt`、`doMgL`、`ph`、`notes`；`doMgL > 0` 且 `ph ∈ [6,9]`，否则返回 **400**；支持 PUT 更新（更新同样受水源确认规则约束）
7. **FeedEvent 投喂**：`pondId`、`fedAt`、`feedType`、`amountKg`、`operatorName`
8. **Dashboard**：塘总数、quarantine 数、近 24h 采样数、近 7 日投喂总量 kg

> 种子数据中「东港潮汐一号场」在 2 小时前刚完成海水源切换（近海沙滤井水 → 外海深管取水），当前仍在 24 小时确认窗内：对其下属塘口（A-01、A-02）登记或修改水质样时，水源确认须填写 `外海深管取水`。

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
