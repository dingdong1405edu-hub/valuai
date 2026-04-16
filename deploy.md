# Railway + GitHub Deployment Guide — For Claude Agents

> **Mục đích**: Hướng dẫn Claude agents deploy bất kỳ dự án nào lên Railway.
> **Yêu cầu từ user**: Chỉ cần 2 thứ — **GitHub token** (`ghp_xxx`) và **Railway API token** (UUID).
> **Railway CLI KHÔNG đáng tin** — luôn dùng **GraphQL API trực tiếp**.

---

## Thông tin cố định (không đổi giữa các dự án)

```
Railway email       : dingdong1405edu@gmail.com
Railway Workspace ID: fa660a6f-4e10-4c0d-b7a1-6db8055986e8
GitHub username     : dingdong1405edu-hub
Git user.email      : dingdong1405edu@gmail.com
Git user.name       : DingDong
```

---

## Quy trình tổng quan

```
Hỏi user 2 token → Chuẩn bị code → Push GitHub → Tạo Railway project
→ Tạo service → Set branch → Tạo domain → Set env vars → Trigger deploy
→ Theo dõi build → Fix lỗi nếu có → Verify production
```

**Thời gian**: Build lần đầu ~5-8 phút (Dockerfile) hoặc ~8-12 phút (Nixpacks, tải nixpkgs). Các lần sau ~2-3 phút nhờ cache.

---

## BƯỚC 0: Hỏi user lấy 2 token

```
Tôi cần 2 mã để deploy:
1. GitHub Personal Access Token (ghp_xxx) — tạo tại https://github.com/settings/tokens
2. Railway API Token (UUID) — tạo tại https://railway.app/account/tokens
```

Lưu vào biến:
```bash
GH_TOKEN="ghp_xxx..."
RW_TOKEN="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### Test cả 2 token ngay:

```bash
# Test GitHub
curl -s -H "Authorization: token $GH_TOKEN" https://api.github.com/user \
  | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log('GitHub OK:',JSON.parse(d).login))"

# Test Railway
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ me { id email } }"}'
# Expect: {"data":{"me":{"id":"...","email":"..."}}}
```

> **Nếu Railway trả `Unauthorized`**: Token sai hoặc hết hạn. Yêu cầu user tạo token mới.
> **KHÔNG dùng Railway CLI** (`railway list`, `railway up`...) — CLI không nhận token dạng UUID, chỉ hoạt động ở interactive mode.

---

## BƯỚC 1: Chuẩn bị code

### 1.1 Chọn build strategy (QUAN TRỌNG — đọc kỹ)

Có 2 cách để Railway biết dùng Node 20. **Chọn đúng ngay từ đầu**, đừng mix 2 cách:

---

#### CÁCH A — Dockerfile (KHUYẾN NGHỊ, đáng tin nhất)

Tạo file `Dockerfile` ở root:

```dockerfile
FROM node:20-alpine

RUN apk add --no-cache openssl libc6-compat

WORKDIR /app

COPY package*.json ./
COPY prisma ./prisma/
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3000
ENV PORT=3000
ENV NODE_ENV=production

CMD ["sh", "-c", "npx prisma db push --accept-data-loss && npm start"]
```

> Nếu không dùng Prisma, đơn giản hóa:
> ```dockerfile
> FROM node:20-alpine
> WORKDIR /app
> COPY package*.json ./
> RUN npm ci
> COPY . .
> RUN npm run build
> EXPOSE 3000
> ENV PORT=3000
> ENV NODE_ENV=production
> CMD ["npm", "start"]
> ```

**`railway.toml`** — KHÔNG chỉ định `builder`, để Railway tự detect Dockerfile:
```toml
[deploy]
restartPolicyType = "always"
restartPolicyMaxRetries = 3
```

> **CẢNH BÁO**: Nếu `railway.toml` có `builder = "nixpacks"` → Railway sẽ BỎ QUA Dockerfile hoàn toàn dù file đó tồn tại. Phải xóa dòng đó.

---

#### CÁCH B — nixpacks.toml (dự phòng khi không muốn dùng Dockerfile)

```toml
[phases.setup]
nixPkgs = ["nodejs-20_x", "npm-9_x"]

[phases.build]
cmds = ["npx prisma generate", "npm run build"]
# Nếu không dùng Prisma: cmds = ["npm run build"]

[start]
cmd = "npx prisma db push --accept-data-loss && npm start"
# Nếu không dùng Prisma: cmd = "npm start"
```

> **BẪY PACKAGE NAME**: Tên Nix package là `nodejs-20_x` (có dấu gạch ngang trước số version) và `npm-9_x`, KHÔNG phải `nodejs_20` hay `npm_10`. Sai tên → build fail với lỗi `derivationStrict` khó debug.

**`railway.toml`** — KHÔNG chỉ định `builder` (để Railway tự nhận nixpacks.toml):
```toml
[deploy]
restartPolicyType = "always"
restartPolicyMaxRetries = 3
```

---

> **VỀ `NIXPACKS_NODE_VERSION=20` ENV VAR**: Đây là cái bẫy. Khi set biến này, Railway Nixpacks v1.38.0 tự động thêm `npm_10` vào package list — nhưng `npm_10` KHÔNG TỒN TẠI trong nixpkgs → build fail ngay bước nix-env install. **Không dùng `NIXPACKS_NODE_VERSION` làm cách chính để set Node version.** Chỉ dùng làm override nếu không có nixpacks.toml.

---

### 1.2 Tạo/kiểm tra các file bắt buộc

**`.gitignore`** (PHẢI có, KHÔNG được commit secrets):
```gitignore
node_modules/
.next/
out/
build/
.env
.env.local
.env.*.local
*.tsbuildinfo
```

**`.node-version`** (hint thêm cho các tool khác):
```
20
```

**`package.json`** — thêm `engines`:
```json
{
  "engines": {
    "node": ">=20.0.0"
  }
}
```

### 1.3 Fix các lỗi phổ biến TRƯỚC KHI deploy

| Kiểm tra | Lệnh/cách fix |
|----------|---------------|
| **NextAuth v5 có `trustHost: true`?** | Thêm vào NextAuth config — **BẮT BUỘC, lỗi #1 phổ biến nhất** |
| Next.js có CVE severity HIGH? | `npm install next@latest` (trong cùng major version) |
| Prisma crash khi build (no DATABASE_URL)? | `export const dynamic = 'force-dynamic'` trên server components hoặc lazy-init Prisma client |
| SDK (Gemini/Groq/Deepgram) crash khi build? | Dùng lazy initialization — chỉ tạo client khi hàm được gọi, không phải lúc module load |

**NextAuth v5 — trustHost (LỖI #1 PHỔ BIẾN NHẤT)**:
```ts
export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: true,    // ← BẮT BUỘC cho Railway/production
  // ... rest of config
})
```

> Nếu thiếu `trustHost: true` → `/api/auth/csrf` trả error JSON thay vì token, login không hoạt động, dashboard redirect loop.

**Prisma lazy init** (nếu Prisma client crash khi build vì không có DATABASE_URL):
```ts
// lib/prisma.ts
import { PrismaClient } from '@prisma/client'
const globalForPrisma = global as unknown as { prisma: PrismaClient }
export const prisma = globalForPrisma.prisma ?? new PrismaClient()
if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma
```

### 1.4 Build local trước

```bash
npm run build
```

> Nếu build local FAIL → fix hết lỗi trước. Đừng push code build fail lên Railway.

---

## BƯỚC 2: Push lên GitHub

```bash
cd /path/to/project

# Init git nếu chưa có
git init
git config user.email "dingdong1405edu@gmail.com"
git config user.name "DingDong"

# Commit tất cả (bao gồm Dockerfile/nixpacks.toml)
git add -A
git commit -m "Deploy to Railway"

# Quyết định branch: dùng main hoặc master, nhất quán
# Nếu dùng main:
git branch -M main
git remote add origin "https://${GH_TOKEN}@github.com/dingdong1405edu-hub/<REPO_NAME>.git" 2>/dev/null \
  || git remote set-url origin "https://${GH_TOKEN}@github.com/dingdong1405edu-hub/<REPO_NAME>.git"
git push -u origin main --force

# Nếu dùng master (repo đã có sẵn trên master):
git remote add origin "https://${GH_TOKEN}@github.com/dingdong1405edu-hub/<REPO_NAME>.git" 2>/dev/null \
  || git remote set-url origin "https://${GH_TOKEN}@github.com/dingdong1405edu-hub/<REPO_NAME>.git"
git push -u origin master --force
```

> **Lưu ý**: Ghi nhớ branch bạn push là `main` hay `master` — bước 3.3 phải set đúng branch đó.

---

## BƯỚC 3: Tạo Railway project + service

### 3.1 Tạo project

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"mutation { projectCreate(input: { name: \\\"<TÊN_PROJECT>\\\", workspaceId: \\\"fa660a6f-4e10-4c0d-b7a1-6db8055986e8\\\" }) { id name environments { edges { node { id name } } } } }\"}"
```

**Lưu lại từ response:**
```
PROJECT_ID = .data.projectCreate.id
ENV_ID     = .data.projectCreate.environments.edges[0].node.id
```

### 3.2 Tạo service (kết nối GitHub repo)

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"mutation { serviceCreate(input: { projectId: \\\"$PROJECT_ID\\\", name: \\\"web\\\", source: { repo: \\\"dingdong1405edu-hub/<REPO_NAME>\\\" } }) { id name } }\"}"
```

**Lưu lại:** `SERVICE_ID = .data.serviceCreate.id`

### 3.3 Set branch đúng (QUAN TRỌNG)

```bash
# Thay "main" bằng "master" nếu bạn push lên master ở bước 2
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"mutation { serviceConnect(id: \\\"$SERVICE_ID\\\", input: { repo: \\\"dingdong1405edu-hub/<REPO_NAME>\\\", branch: \\\"main\\\" }) { id } }\"}"
```

> **KHÔNG BỎ QUA BƯỚC NÀY**. Railway mặc định dùng branch `master`. Nếu code ở `main` mà không set → Railway pull code sai branch → build thành công nhưng deploy code cũ hoặc không có gì.
> Dấu hiệu deploy sai branch: build log thấy `package.json` với tên/version khác với project của bạn.

---

## BƯỚC 4: Tạo domain

**Tạo domain TRƯỚC khi set env vars** (vì cần domain cho NEXTAUTH_URL):

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"mutation { serviceDomainCreate(input: { serviceId: \\\"$SERVICE_ID\\\", environmentId: \\\"$ENV_ID\\\" }) { id domain } }\"}"
```

**Lưu lại:** `DOMAIN = .data.serviceDomainCreate.domain`
(ví dụ: `web-production-4a953.up.railway.app`)

---

## BƯỚC 5: Set environment variables

**LUÔN dùng file JSON tạm** — shell escaping sẽ gây lỗi nếu dùng inline:

```bash
cat > /tmp/rw_vars.json << 'ENDJSON'
{
  "query": "mutation($input: VariableCollectionUpsertInput!) { variableCollectionUpsert(input: $input) }",
  "variables": {
    "input": {
      "projectId": "PROJECT_ID_HERE",
      "environmentId": "ENV_ID_HERE",
      "serviceId": "SERVICE_ID_HERE",
      "variables": {
        "DATABASE_URL": "postgresql://...",
        "AUTH_SECRET": "GENERATE_WITH_openssl_rand_-base64_32",
        "NEXTAUTH_SECRET": "SAME_AS_AUTH_SECRET",
        "NEXTAUTH_URL": "https://DOMAIN_HERE",
        "NEXT_PUBLIC_APP_URL": "https://DOMAIN_HERE",
        "PORT": "3000",
        "NODE_ENV": "production"
      }
    }
  }
}
ENDJSON

# Thay placeholders bằng sed:
sed -i "s/PROJECT_ID_HERE/$PROJECT_ID/g; s/ENV_ID_HERE/$ENV_ID/g; s/SERVICE_ID_HERE/$SERVICE_ID/g; s/DOMAIN_HERE/$DOMAIN/g" /tmp/rw_vars.json

curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/rw_vars.json
# Expect: {"data":{"variableCollectionUpsert":true}}
```

**Env vars quan trọng:**
| Biến | Giá trị | Ghi chú |
|------|---------|---------|
| `PORT` | `3000` | Railway expose port này |
| `NODE_ENV` | `production` | |
| `NEXTAUTH_URL` | `https://<domain>` | PHẢI khớp domain Railway chính xác |
| `AUTH_SECRET` | random 32 bytes | `openssl rand -base64 32` |
| `NEXTAUTH_SECRET` | giống AUTH_SECRET | NextAuth v5 dùng cả 2 |
| `DATABASE_URL` | PostgreSQL URL | Public URL nếu DB ở Railway project khác |

> **KHÔNG cần set `NIXPACKS_NODE_VERSION`** nếu đã dùng Dockerfile hoặc `nixpacks.toml` đúng cách.
> `variableCollectionUpsert` merge vào env hiện có, không ghi đè hết — có thể gọi nhiều lần an toàn.

---

## BƯỚC 6: Trigger deploy

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"mutation { serviceInstanceRedeploy(serviceId: \\\"$SERVICE_ID\\\", environmentId: \\\"$ENV_ID\\\") }\"}"
# Expect: {"data":{"serviceInstanceRedeploy":true}}
```

---

## BƯỚC 7: Theo dõi build (polling)

### Check trạng thái deploy + lấy DEPLOY_ID mới nhất

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"{ deployments(input: { projectId: \\\"$PROJECT_ID\\\", environmentId: \\\"$ENV_ID\\\", serviceId: \\\"$SERVICE_ID\\\" }) { edges { node { id status createdAt } } } }\"}"
```

**Flow trạng thái:** `INITIALIZING` → `BUILDING` → `DEPLOYING` → `SUCCESS` ✅ (hoặc `FAILED` ❌)

Lấy `DEPLOY_ID` từ node đầu tiên (mới nhất).

### Xem build logs (khi BUILDING hoặc FAILED)

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"{ buildLogs(deploymentId: \\\"$DEPLOY_ID\\\") { message severity } }\"}" \
  | grep -o '"message":"[^"]*"' \
  | sed 's/"message":"//;s/"$//' \
  | grep -v "deleting\|nix-store\|hard link\|note:" \
  | tail -40
```

> Dấu hiệu build tốt:
> - Dockerfile: log đầu tiên là `Using Detected Dockerfile` + `FROM docker.io/library/node:20-alpine`
> - Nixpacks: `setup │ nodejs-20_x, npm-9_x` (không thấy `npm_10`)

### Xem runtime logs (khi SUCCESS nhưng app crash ngay)

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"{ deploymentLogs(deploymentId: \\\"$DEPLOY_ID\\\") { message severity } }\"}" \
  | grep -o '"message":"[^"]*"' | sed 's/"message":"//;s/"$//' | tail -30
```

---

## BƯỚC 8: Verify production

```bash
PROD="https://$DOMAIN"

# 1. Pages cơ bản
curl -s -o /dev/null -w "/ → %{http_code}\n" "$PROD/"
curl -s -o /dev/null -w "/login → %{http_code}\n" "$PROD/login"
curl -s -o /dev/null -w "/dashboard (protected) → %{http_code}\n" "$PROD/dashboard"
# Expect: 200, 200, 307

# 2. NextAuth CSRF (xác nhận trustHost hoạt động)
curl -s "$PROD/api/auth/csrf"
# Expect: {"csrfToken":"...hex..."} — nếu thấy JSON error → trustHost chưa được set

# 3. API auth guard
curl -s -o /dev/null -w "/api/ai/score (unauth) → %{http_code}\n" -X POST "$PROD/api/ai/score"
# Expect: 401
```

---

## Troubleshooting — Bảng tra lỗi nhanh

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| `Node.js 18.x, required >=20` | Railway dùng Node 18 | Dùng Dockerfile (`FROM node:20-alpine`) hoặc `nixpacks.toml` với `nodejs-20_x` |
| Build fail ở `nix-env install`, lỗi `derivationStrict` | Package name Nix sai | Kiểm tra nixpacks.toml: phải là `nodejs-20_x` và `npm-9_x` (có gạch ngang), không phải `nodejs_20`/`npm_10` |
| Build log: `Using Nixpacks` dù có Dockerfile | `railway.toml` có `builder = "nixpacks"` | Xóa dòng `builder` khỏi railway.toml, hoặc xóa toàn bộ `[build]` section |
| `UntrustedHost` / `/api/auth/csrf` trả JSON error | NextAuth v5 chặn domain Railway | Thêm `trustHost: true` vào NextAuth config |
| `/api/auth/csrf` trả `{"error":"..."}` không có csrfToken | `AUTH_SECRET` chưa set hoặc `NEXTAUTH_URL` sai | Check env vars: AUTH_SECRET, NEXTAUTH_URL phải khớp domain |
| Build log thấy tên project/version khác | Deploy sai branch | Dùng `serviceConnect` set đúng branch (`main` hoặc `master`) |
| `DATABASE_URL not found` khi build | Prisma cần DB URL lúc build | Dùng `export const dynamic = 'force-dynamic'` hoặc lazy init Prisma |
| Deploy status `SKIPPED` | Có deploy khác đang chạy | Đợi xong rồi redeploy |
| `EPERM` khi prisma generate | Dev server đang chạy giữ file lock | Kill dev server trước khi build |
| App crash ngay sau SUCCESS | Runtime error (env var thiếu, DB unreachable) | Xem `deploymentLogs` không phải `buildLogs` |
| `Severity: HIGH — CVE-xxx` | Package có lỗ hổng | `npm install <package>@latest` trong cùng major version |

---

## Sửa lỗi nâng cao — Clear nixpacksPlan override

Nếu đã lỡ set `nixpacksPlan` qua API và muốn Railway đọc lại `nixpacks.toml` hoặc Dockerfile:

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation U($s:String!,$e:String!,$i:ServiceInstanceUpdateInput!){serviceInstanceUpdate(serviceId:$s,environmentId:$e,input:$i)}",
    "variables": {
      "s": "SERVICE_ID",
      "e": "ENV_ID",
      "i": { "nixpacksPlan": null, "buildCommand": "", "startCommand": "" }
    }
  }'
```

> **Lưu ý format nixpacksPlan khi set qua API** (nếu cần):
> ```json
> {
>   "phases": {
>     "setup": { "nixPkgs": ["nodejs-20_x", "openssl"] },
>     "install": { "cmds": ["npm ci"] },
>     "build": { "cmds": ["npm run build"] }
>   },
>   "start": { "cmd": "npm start" }
> }
> ```
> Field `start` PHẢI là object `{"cmd": "..."}`, không phải string thuần. Sai → build fail với `invalid type: string`.

---

## Quy trình cập nhật code (re-deploy)

Sau khi đã deploy lần đầu, mỗi lần cập nhật chỉ cần:

```bash
# 1. Commit + push
git add -A
git commit -m "update: mô tả thay đổi"
git push origin main   # hoặc master

# 2. Trigger redeploy (Railway có thể tự trigger nếu GitHub webhook đã set,
#    nhưng gọi thủ công cho chắc)
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"mutation { serviceInstanceRedeploy(serviceId: \\\"$SERVICE_ID\\\", environmentId: \\\"$ENV_ID\\\") }\"}"

# 3. Poll cho đến SUCCESS
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"{ deployments(input: { projectId: \\\"$PROJECT_ID\\\", environmentId: \\\"$ENV_ID\\\", serviceId: \\\"$SERVICE_ID\\\" }) { edges { node { id status } } } }\"}"
```

---

## Thêm env vars sau deploy

```bash
cat > /tmp/rw_extra.json << 'ENDJSON'
{
  "query": "mutation($input: VariableCollectionUpsertInput!) { variableCollectionUpsert(input: $input) }",
  "variables": {
    "input": {
      "projectId": "PROJECT_ID",
      "environmentId": "ENV_ID",
      "serviceId": "SERVICE_ID",
      "variables": {
        "NEW_VAR": "value"
      }
    }
  }
}
ENDJSON

curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RW_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/rw_extra.json
```

> Thêm env var **KHÔNG** tự động redeploy. Phải gọi `serviceInstanceRedeploy` thủ công sau đó.

---

## Checklist tóm tắt

```
[ ] Hỏi user: GH_TOKEN + RW_TOKEN, test cả 2
[ ] Chọn build strategy: Dockerfile (khuyến nghị) hoặc nixpacks.toml
[ ] Chuẩn bị: .gitignore, .node-version, engines trong package.json
[ ] Fix bắt buộc: trustHost: true (NextAuth), lazy init (Prisma/SDK)
[ ] railway.toml: KHÔNG có builder = "nixpacks"
[ ] Build local pass (npm run build)
[ ] Tạo GitHub repo nếu chưa có
[ ] Push GitHub lên đúng branch (main hoặc master)
[ ] Tạo Railway project → lưu PROJECT_ID, ENV_ID
[ ] Tạo service → lưu SERVICE_ID
[ ] serviceConnect → set đúng branch (main hoặc master)
[ ] serviceDomainCreate → lưu DOMAIN
[ ] Set env vars qua /tmp/rw_vars.json
[ ] serviceInstanceRedeploy
[ ] Poll: INITIALIZING → BUILDING → DEPLOYING → SUCCESS
[ ] Verify: http_code /, /login, /dashboard (307), /api/auth/csrf (csrfToken)
[ ] Báo user URL production
```

---

## Ghi chú cho Claude agents

1. **Chỉ cần 2 token** — GitHub (`ghp_xxx`) và Railway (UUID). Hỏi user ngay đầu.
2. **KHÔNG dùng Railway CLI** — luôn dùng GraphQL API (`https://backboard.railway.app/graphql/v2`).
3. **LUÔN dùng file JSON tạm** (`/tmp/rw_vars.json`) khi gọi `variableCollectionUpsert` — tránh shell escaping hell với special chars trong secrets.
4. **Dockerfile > nixpacks.toml** — Dockerfile với `node:20-alpine` đơn giản và đáng tin hơn. Dùng khi nixpacks gặp vấn đề.
5. **KHÔNG để `builder = "nixpacks"` trong railway.toml** — nó chặn Railway detect Dockerfile.
6. **LUÔN set branch** bằng `serviceConnect` — Railway mặc định `master`, code có thể ở `main`.
7. **LUÔN thêm `trustHost: true`** vào NextAuth trước khi deploy — lỗi #1 phổ biến nhất, khó debug sau khi deploy.
8. **Tạo domain TRƯỚC khi set env vars** — cần domain cho `NEXTAUTH_URL`.
9. **Build lần đầu chậm 5-8 phút** — không phải lỗi, đừng cancel.
10. **Không commit `.env.local`** — chứa secrets.
11. **Sau khi thêm env var** → PHẢI redeploy thủ công.
12. **Khi debug**: `buildLogs` cho build errors, `deploymentLogs` cho runtime errors (app crash sau khi deploy).
13. **`NIXPACKS_NODE_VERSION=20` gây bẫy** — env var này khiến Nixpacks v1.38.0 tự thêm `npm_10` (không tồn tại trong nixpkgs) → fail. Không dùng env var này; dùng `nixpacks.toml` hoặc Dockerfile thay thế.
