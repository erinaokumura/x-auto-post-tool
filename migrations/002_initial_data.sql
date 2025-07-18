-- 初期データ投入スクリプト
-- 作成日: 2024年
-- 説明: x-auto-post-toolの初期データ投入

-- テスト用ユーザーの作成
INSERT INTO users (email, username, display_name, is_active, is_verified) VALUES
('test@example.com', 'testuser', 'テストユーザー', TRUE, TRUE),
('admin@example.com', 'admin', '管理者', TRUE, TRUE);

-- デフォルト設定の挿入
-- テストユーザー用の設定
INSERT INTO user_settings (user_id, setting_key, setting_value, setting_type, description) VALUES
(1, 'default_language', 'ja', 'string', 'デフォルトの投稿言語'),
(1, 'auto_post_enabled', 'true', 'boolean', '自動投稿の有効/無効'),
(1, 'max_retry_count', '3', 'integer', '最大リトライ回数'),
(1, 'notification_enabled', 'true', 'boolean', '通知の有効/無効'),
(1, 'tweet_template', '🎉 {repository} の開発進捗\n\n{commit_message}\n\n#個人開発 #プログラミング', 'string', 'ツイートテンプレート'),
(1, 'hashtags', '["個人開発", "プログラミング", "GitHub"]', 'json', 'デフォルトハッシュタグ');

-- 管理者用の設定
INSERT INTO user_settings (user_id, setting_key, setting_value, setting_type, description) VALUES
(2, 'default_language', 'ja', 'string', 'デフォルトの投稿言語'),
(2, 'auto_post_enabled', 'true', 'boolean', '自動投稿の有効/無効'),
(2, 'max_retry_count', '5', 'integer', '最大リトライ回数'),
(2, 'notification_enabled', 'true', 'boolean', '通知の有効/無効'),
(2, 'tweet_template', '🚀 {repository} の開発進捗\n\n{commit_message}\n\n#個人開発 #プログラミング #OSS', 'string', 'ツイートテンプレート'),
(2, 'hashtags', '["個人開発", "プログラミング", "OSS", "GitHub"]', 'json', 'デフォルトハッシュタグ');

-- サンプル投稿履歴の作成（テスト用）
INSERT INTO post_history (user_id, repository, commit_message, tweet_text, tweet_id, language, status, posted_at) VALUES
(1, 'testuser/my-project', 'feat: 新機能を追加', '🎉 testuser/my-project の開発進捗

feat: 新機能を追加

#個人開発 #プログラミング', '1234567890123456789', 'ja', 'success', CURRENT_TIMESTAMP - INTERVAL '1 day'),
(1, 'testuser/my-project', 'fix: バグを修正', '🎉 testuser/my-project の開発進捗

fix: バグを修正

#個人開発 #プログラミング', '1234567890123456790', 'ja', 'success', CURRENT_TIMESTAMP - INTERVAL '2 days'),
(2, 'admin/awesome-project', 'docs: ドキュメントを更新', '🚀 admin/awesome-project の開発進捗

docs: ドキュメントを更新

#個人開発 #プログラミング #OSS', '1234567890123456791', 'ja', 'success', CURRENT_TIMESTAMP - INTERVAL '3 days');

-- 失敗例の投稿履歴（テスト用）
INSERT INTO post_history (user_id, repository, commit_message, tweet_text, language, status, error_message, retry_count) VALUES
(1, 'testuser/failed-project', 'feat: 失敗する投稿', '🎉 testuser/failed-project の開発進捗

feat: 失敗する投稿

#個人開発 #プログラミング', 'ja', 'failed', 'API rate limit exceeded', 3);

-- 保留中の投稿履歴（テスト用）
INSERT INTO post_history (user_id, repository, commit_message, tweet_text, language, status) VALUES
(1, 'testuser/pending-project', 'feat: 保留中の投稿', '🎉 testuser/pending-project の開発進捗

feat: 保留中の投稿

#個人開発 #プログラミング', 'ja', 'pending');

-- 英語版のサンプル投稿履歴
INSERT INTO post_history (user_id, repository, commit_message, tweet_text, tweet_id, language, status, posted_at) VALUES
(2, 'admin/english-project', 'feat: add new feature', '🚀 admin/english-project development progress

feat: add new feature

#indiedev #programming #OSS', '1234567890123456792', 'en', 'success', CURRENT_TIMESTAMP - INTERVAL '4 days');

-- コメント追加
COMMENT ON TABLE users IS 'ユーザー情報テーブル - 初期データ投入済み';
COMMENT ON TABLE user_settings IS 'ユーザー設定テーブル - デフォルト設定投入済み';
COMMENT ON TABLE post_history IS '投稿履歴テーブル - サンプルデータ投入済み'; 