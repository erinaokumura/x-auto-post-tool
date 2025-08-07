'use client'

import { useState, useEffect, useRef } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'

export default function CallbackPage() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')
  const searchParams = useSearchParams()
  const router = useRouter()
  const hasProcessed = useRef(false) // 重複実行を防ぐフラグ

  useEffect(() => {
    const handleCallback = async () => {
      // 既に処理済みの場合は何もしない
      if (hasProcessed.current) {
        return
      }

      const code = searchParams.get('code')
      const state = searchParams.get('state')

      if (!code || !state) {
        setStatus('error')
        setMessage('認証パラメータが不足しています')
        return
      }

      // 処理開始前にフラグを設定
      hasProcessed.current = true

      try {
        const response = await fetch('/api/auth/twitter/callback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code, state }),
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || `認証に失敗しました: ${response.status}`)
        }

        const data = await response.json()
        setStatus('success')
        setMessage('認証が完了しました！ダッシュボードにリダイレクトします...')

        // 3秒後にダッシュボードにリダイレクト
        setTimeout(() => {
          router.push('/dashboard')
        }, 3000)

      } catch (error) {
        console.error('コールバック処理エラー:', error)
        setStatus('error')
        setMessage(error instanceof Error ? error.message : '予期しないエラーが発生しました')
        // エラー時はフラグをリセット（リトライ可能にする）
        hasProcessed.current = false
      }
    }

    handleCallback()
  }, [searchParams, router])

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            認証処理中
          </h1>

          {status === 'loading' && (
            <div className="mb-6">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">認証情報を処理しています...</p>
            </div>
          )}

          {status === 'success' && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center justify-center mb-2">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-green-800 font-medium">認証成功!</p>
              <p className="text-green-700 text-sm mt-1">{message}</p>
            </div>
          )}

          {status === 'error' && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-center justify-center mb-2">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <p className="text-red-800 font-medium">認証エラー</p>
              <p className="text-red-700 text-sm mt-1">{message}</p>
            </div>
          )}

          <div className="space-y-3">
            {status === 'success' && (
              <Link
                href="/dashboard"
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 transition duration-200 block text-center"
              >
                ダッシュボードへ
              </Link>
            )}

            {status === 'error' && (
              <>
                <Link
                  href="/login"
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 transition duration-200 block text-center"
                >
                  再度ログイン
                </Link>
                <Link
                  href="/"
                  className="w-full bg-gray-100 text-gray-700 py-3 px-4 rounded-md hover:bg-gray-200 transition duration-200 block text-center"
                >
                  ホームに戻る
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </main>
  )
} 