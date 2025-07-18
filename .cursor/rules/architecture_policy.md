# Rule: architecture_policy

## 概要
このルールは「x-auto-post-tool」プロジェクトのアーキテクチャ設計方針・技術選定理由・運用戦略に基づき、AIによるコード生成・修正時の品質と一貫性を担保するためのものです。

## 適用範囲
- コード生成・修正・設計提案・リファクタリング・テスト作成時
- FastAPI＋PostgreSQL＋Redis＋Celery＋Next.js＋Vercel＋Railway構成

## ガイドライン
- 設計思想・技術選定理由（docs/architecture_design.md）に反しないこと
- モジュール分割・責務分離を優先し、保守性・拡張性を重視する
- セキュリティ（OAuth2.0 PKCE, JWT, HTTPS, .env管理, DB暗号化, 最小権限）を常に考慮
- テスト・CI/CD・依存管理・環境変数管理を厳守
- コスト効率・運用負荷最小化を意識した構成を提案
- スケーラビリティ（Celery/Redis/PostgreSQLの水平・垂直スケーリング）を考慮
- 既存設計（architecture_design.md）と矛盾しないこと

## 参考
- docs/architecture_design.md
- https://docs.cursor.com/context/rules

---
このルールはAIによるコード生成・修正・設計提案時の必須参照ドキュメントとします。 