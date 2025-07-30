'use client'

import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            X Auto Post Tool
          </h1>
          <p className="text-gray-600 mb-8">
            GitHubのコミットをAIで最適化してXに自動投稿
          </p>
          
          <div className="space-y-4">
            <Link
              href="/login"
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 transition duration-200 block text-center"
            >
              ログイン
            </Link>
            
            <div className="text-sm text-gray-500">
              <p>または</p>
            </div>
            
            <Link
              href="/dashboard"
              className="w-full bg-gray-100 text-gray-700 py-3 px-4 rounded-md hover:bg-gray-200 transition duration-200 block text-center"
            >
              ダッシュボード（開発用）
            </Link>
          </div>
        </div>
      </div>
    </main>
  )
} 