// API設定とユーティリティ関数

/**
 * バックエンドAPIのベースURL
 * 本番環境ではNEXT_PUBLIC_API_URLを使用し、開発環境ではBACKEND_URLまたはlocalhostを使用
 */
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || 'http://localhost:8000'

/**
 * APIリクエストのデフォルト設定
 */
export const DEFAULT_FETCH_OPTIONS: RequestInit = {
  credentials: 'include', // セッションクッキーを含める
  headers: {
    'Content-Type': 'application/json',
  },
}

/**
 * APIエンドポイントのパスを生成
 */
export const createApiUrl = (path: string): string => {
  // パスが/で始まらない場合は追加
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL}${normalizedPath}`
}

/**
 * APIリクエストを送信するヘルパー関数
 */
export const apiRequest = async (
  path: string,
  options: RequestInit = {}
): Promise<Response> => {
  const url = createApiUrl(path)
  const mergedOptions = {
    ...DEFAULT_FETCH_OPTIONS,
    ...options,
    headers: {
      ...DEFAULT_FETCH_OPTIONS.headers,
      ...(options.headers || {}),
    },
  }
  
  return fetch(url, mergedOptions)
}

/**
 * JSONレスポンスを期待するAPIリクエスト
 */
export const apiRequestJson = async <T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> => {
  const response = await apiRequest(path, options)
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `APIリクエストに失敗しました: ${response.status}`)
  }
  
  return response.json()
}
