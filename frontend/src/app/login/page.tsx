'use client'

import { useState } from 'react'
import Link from 'next/link'

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [authStatus, setAuthStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const handleTwitterLogin = async () => {
    setIsLoading(true)
    setAuthStatus('loading')
    setErrorMessage('')

    try {
      // 環境変数からバックエンドURLを取得
      const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
      console.log('🔧 Frontend - Backend URL:', backendUrl);
      
      // FastAPIのTwitter認証エンドポイントを直接呼び出し
      const response = await fetch(`${backendUrl}/api/auth/twitter/login`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // CORS設定
        mode: 'cors',
      })

      if (!response.ok) {
        throw new Error(`認証リクエストに失敗しました: ${response.status}`)
      }

      const data = await response.json()
      
      if (data.authorization_url) {
        setAuthStatus('success')
        // Twitter認証ページにリダイレクト
        window.location.href = data.authorization_url
      } else {
        throw new Error('認証URLが取得できませんでした')
      }
    } catch (error) {
      console.error('Twitter認証エラー:', error)
      setAuthStatus('error')
      setErrorMessage(error instanceof Error ? error.message : '予期しないエラーが発生しました')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            ログイン
          </h1>
          <p className="text-gray-600 mb-8">
            Xアカウントでログインしてください
          </p>

          {/* 認証状態表示 */}
          {authStatus === 'loading' && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-blue-800">認証処理中...</p>
            </div>
          )}

          {authStatus === 'error' && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-800 text-sm">{errorMessage}</p>
            </div>
          )}

          {authStatus === 'success' && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
              <p className="text-green-800">Xにリダイレクトしています...</p>
            </div>
          )}

          <div className="space-y-4">
            <button
              onClick={handleTwitterLogin}
              disabled={isLoading}
              className={`w-full py-3 px-4 rounded-md transition duration-200 ${
                isLoading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-black hover:bg-gray-800'
              } text-white font-medium`}
            >
              {isLoading ? '処理中...' : 'X (Twitter) でログイン'}
            </button>

            <Link
              href="/"
              className="w-full bg-gray-100 text-gray-700 py-3 px-4 rounded-md hover:bg-gray-200 transition duration-200 block text-center"
            >
              ホームに戻る
            </Link>
          </div>

          <div className="mt-8 text-xs text-gray-500">
            <p>
              ログインすることで、GitHubのコミット情報を取得し、
              AIで生成されたツイートをXに投稿することに同意したものとみなします。
            </p>
          </div>
        </div>
      </div>
    </main>
  )
} 