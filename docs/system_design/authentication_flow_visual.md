# 認証フロー（視覚的版）

## システム構成図

```mermaid
graph TB
    subgraph "Client Side"
        User[👤 User<br/>Browser]
        Frontend[🖥️ Frontend<br/>Next.js<br/>localhost:3000]
    end
    
    subgraph "Server Side"
        Backend[⚙️ Backend<br/>FastAPI<br/>Railway App]
        Redis[📦 Redis<br/>Session Store<br/>Railway Redis]
        DB[🗄️ PostgreSQL<br/>User Data<br/>Railway DB]
    end
    
    subgraph "External APIs"
        Twitter[🐦 Twitter API<br/>OAuth 2.0<br/>Tweet Posting]
        GitHub[😺 GitHub API<br/>Repository<br/>Commit Data]
        OpenAI[🤖 OpenAI API<br/>GPT-4<br/>Tweet Generation]
    end
    
    User --> Frontend
    Frontend <--> Backend
    Backend <--> Redis
    Backend <--> DB
    Backend <--> Twitter
    Backend <--> GitHub
    Backend <--> OpenAI
    
    style User fill:#e3f2fd
    style Frontend fill:#f3e5f5
    style Backend fill:#e8f5e8
    style Redis fill:#fff3e0
    style DB fill:#fce4ec
    style Twitter fill:#e1f5fe
    style GitHub fill:#f1f8e9
    style OpenAI fill:#e8eaf6
```

## 認証フロー詳細

```mermaid
sequenceDiagram
    participant 👤 as 👤 User
    participant 🖥️ as 🖥️ Frontend
    participant ⚙️ as ⚙️ Backend
    participant 📦 as 📦 Redis
    participant 🗄️ as 🗄️ Database
    participant 🐦 as 🐦 Twitter

    👤->>🖥️: 1. ログインボタンクリック
    🖥️->>⚙️: 2. GET /api/auth/twitter/login
    
    ⚙️->>📦: 3. OAuth state生成・保存
    📦-->>⚙️: 4. state保存完了
    
    ⚙️->>🐦: 5. 認証URL取得要求
    🐦-->>⚙️: 6. authorization_url返却
    
    ⚙️-->>🖥️: 7. {authorization_url}
    🖥️->>👤: 8. Twitter認証ページリダイレクト
    
    👤->>🐦: 9. 認証・アプリ許可
    🐦->>⚙️: 10. コールバック<br/>GET /callback?code=xxx&state=yyy
    
    ⚙️->>🖥️: 11. フロントエンドリダイレクト<br/>/callback?code=xxx&state=yyy
    
    🖥️->>⚙️: 12. POST /api/auth/twitter/callback<br/>{code, state}
    
    ⚙️->>📦: 13. state検証
    📦-->>⚙️: 14. 検証結果
    
    ⚙️->>🐦: 15. アクセストークン取得
    🐦-->>⚙️: 16. access_token
    
    ⚙️->>🐦: 17. ユーザー情報取得
    🐦-->>⚙️: 18. user_info
    
    ⚙️->>🗄️: 19. ユーザー作成/更新
    🗄️-->>⚙️: 20. 保存完了
    
    ⚙️->>📦: 21. セッション作成
    📦-->>⚙️: 22. session_id
    
    ⚙️-->>🖥️: 23. Set-Cookie: session_id<br/>認証成功レスポンス
    
    🖥️->>👤: 24. ダッシュボードリダイレクト
```

## ツイート投稿フロー

```mermaid
flowchart TD
    Start([🚀 ツイート生成開始]) --> Input[📝 リポジトリ名入力]
    
    Input --> Auth{🔐 認証チェック}
    Auth -->|❌ 未認証| Login[🔑 ログインページ]
    Auth -->|✅ 認証済み| GitHub
    
    Login --> OAuth[🐦 Twitter OAuth]
    OAuth --> Auth
    
    GitHub[😺 GitHub API<br/>最新コミット取得] --> OpenAI[🤖 OpenAI API<br/>ツイート文生成]
    
    OpenAI --> Preview[👀 プレビュー表示]
    Preview --> Edit[✏️ ユーザー編集]
    
    Edit --> Confirm{📤 投稿確認}
    Confirm -->|❌ キャンセル| Preview
    Confirm -->|✅ 投稿| Post[🐦 Twitter投稿]
    
    Post --> Success{📊 投稿結果}
    Success -->|✅ 成功| Result[🎉 投稿成功表示]
    Success -->|❌ 失敗| Error[⚠️ エラー表示]
    
    Error --> Preview
    Result --> End([🏁 完了])
    
    style Start fill:#e8f5e8
    style Auth fill:#fff3e0
    style GitHub fill:#f1f8e9
    style OpenAI fill:#e8eaf6
    style Post fill:#e1f5fe
    style Result fill:#e8f5e8
    style Error fill:#ffebee
```

## データフロー図

```mermaid
graph LR
    subgraph "Input"
        Repo[📁 Repository<br/>owner/repo]
    end
    
    subgraph "Processing"
        API1[😺 GitHub API] --> Commit[📝 Commit Info]
        Commit --> API2[🤖 OpenAI API]
        API2 --> Tweet[💬 Tweet Draft]
    end
    
    subgraph "User Interaction"
        Tweet --> Edit[✏️ Edit]
        Edit --> Final[📤 Final Tweet]
    end
    
    subgraph "Output"
        Final --> API3[🐦 Twitter API]
        API3 --> Published[🌐 Published Tweet]
    end
    
    Repo --> API1
    
    style Repo fill:#f1f8e9
    style Commit fill:#e8eaf6
    style Tweet fill:#fff3e0
    style Final fill:#e1f5fe
    style Published fill:#e8f5e8
```

## エラーハンドリング

```mermaid
graph TD
    Request[📨 API Request] --> Check{🔍 Check}
    
    Check -->|✅ Success| Process[⚙️ Process]
    Check -->|🔐 Auth Error| Auth[🔑 401 Unauthorized]
    Check -->|⏰ Rate Limit| Rate[🚫 429 Rate Limited]
    Check -->|💥 Server Error| Server[❌ 500 Server Error]
    
    Process --> Success[✅ Success Response]
    
    Auth --> Login[🔑 Redirect to Login]
    Rate --> Retry[⏳ Circuit Breaker<br/>Retry Later]
    Server --> Log[📝 Error Logging]
    
    Log --> Fallback[🔄 Fallback Response]
    
    style Request fill:#e3f2fd
    style Success fill:#e8f5e8
    style Auth fill:#fff3e0
    style Rate fill:#ffecb3
    style Server fill:#ffebee
```

## セキュリティレイヤー

```
┌─────────────────────────────────────────────────────────┐
│                    🛡️ Security Layers                    │
├─────────────────────────────────────────────────────────┤
│ 🌐 HTTPS/TLS Encryption                                │
├─────────────────────────────────────────────────────────┤
│ 🚫 CORS Policy                                         │
│   • localhost:3000 (dev)                               │
│   • *.railway.app (prod)                               │
├─────────────────────────────────────────────────────────┤
│ ⏰ Rate Limiting                                        │
│   • OAuth: 30/min                                      │
│   • Tweet: 10/min                                      │
├─────────────────────────────────────────────────────────┤
│ 🔐 Session Management                                   │
│   • HttpOnly Cookies                                   │
│   • SameSite=None (prod)                               │
│   • Secure=True (prod)                                 │
├─────────────────────────────────────────────────────────┤
│ 🔒 Token Encryption                                     │
│   • AES-256 Encryption                                 │
│   • Database Storage                                    │
├─────────────────────────────────────────────────────────┤
│ 🔄 Circuit Breaker                                      │
│   • Auto-recovery                                      │
│   • Failure Threshold                                  │
└─────────────────────────────────────────────────────────┘
```
