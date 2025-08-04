'use client'

import { useState } from 'react'
import Link from 'next/link'

interface TweetResponse {
  tweet_text: string
  commit_message: string
  repository: string
}

interface PostResponse {
  success: boolean
  tweet_id?: string
  message: string
}

export default function DashboardPage() {
  const [repository, setRepository] = useState('')
  const [language, setLanguage] = useState('ja')
  const [isGenerating, setIsGenerating] = useState(false)
  const [isPosting, setIsPosting] = useState(false)
  const [generatedTweet, setGeneratedTweet] = useState<TweetResponse | null>(null)
  const [editableTweetText, setEditableTweetText] = useState('')
  const [postResult, setPostResult] = useState<PostResponse | null>(null)
  const [error, setError] = useState('')

  const generateTweet = async () => {
    if (!repository.trim()) {
      setError('リポジトリ名を入力してください')
      return
    }

    setIsGenerating(true)
    setError('')
    setGeneratedTweet(null)
    setEditableTweetText('')
    setPostResult(null)

    try {
      const response = await fetch('/api/generate_tweet', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          repository: repository.trim(),
          language: language 
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `ツイート生成に失敗しました: ${response.status}`)
      }

      const data = await response.json()
      setGeneratedTweet(data)
      setEditableTweetText(data.tweet_text)
    } catch (error) {
      console.error('ツイート生成エラー:', error)
      setError(error instanceof Error ? error.message : '予期しないエラーが発生しました')
    } finally {
      setIsGenerating(false)
    }
  }

  const postTweet = async () => {
    if (!generatedTweet || !editableTweetText?.trim()) return

    setIsPosting(true)
    setError('')
    setPostResult(null)

    try {
      const response = await fetch('/api/post_tweet', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          tweet_text: editableTweetText 
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `ツイート投稿に失敗しました: ${response.status}`)
      }

      const data = await response.json()
      setPostResult(data)
    } catch (error) {
      console.error('ツイート投稿エラー:', error)
      setError(error instanceof Error ? error.message : '予期しないエラーが発生しました')
    } finally {
      setIsPosting(false)
    }
  }

  // 安全にバリデーションを行うヘルパー関数
  const isValidTweet = () => {
    if (!editableTweetText) return false
    const trimmed = editableTweetText.trim()
    return trimmed.length > 0 && trimmed.length <= 280
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                X Auto Post Tool
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/login"
                className="text-gray-500 hover:text-gray-700"
              >
                ログアウト
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">
              ツイート生成・投稿
            </h2>
            <p className="mt-1 text-sm text-gray-600">
              GitHubリポジトリのコミット情報からAIでツイートを生成し、Xに投稿します
            </p>
          </div>

          <div className="p-6 space-y-6">
            {/* 入力フォーム */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="repository" className="block text-sm font-medium text-gray-700">
                  GitHubリポジトリ
                </label>
                <input
                  type="text"
                  id="repository"
                  value={repository}
                  onChange={(e) => setRepository(e.target.value)}
                  placeholder="例: owner/repository-name"
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="language" className="block text-sm font-medium text-gray-700">
                  言語
                </label>
                <select
                  id="language"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="ja">日本語</option>
                  <option value="en">English</option>
                </select>
              </div>
            </div>

            {/* エラー表示 */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            )}

            {/* アクションボタン */}
            <div className="flex space-x-4">
              <button
                onClick={generateTweet}
                disabled={isGenerating}
                className={`px-4 py-2 rounded-md font-medium ${
                  isGenerating
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700'
                } text-white`}
              >
                {isGenerating ? '生成中...' : 'ツイート生成'}
              </button>

              {generatedTweet && (
                <button
                  onClick={postTweet}
                  disabled={isPosting || !isValidTweet()}
                  className={`px-4 py-2 rounded-md font-medium ${
                    isPosting || !isValidTweet()
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-green-600 hover:bg-green-700'
                  } text-white`}
                >
                  {isPosting ? '投稿中...' : 'Xに投稿'}
                </button>
              )}
            </div>

            {/* 生成されたツイート表示・編集 */}
            {generatedTweet && (
              <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-2">生成されたツイート</h3>
                <div className="mb-3">
                  <label htmlFor="tweetEdit" className="block text-xs font-medium text-gray-700 mb-1">
                    ツイート内容（編集可能）
                  </label>
                  <textarea
                    id="tweetEdit"
                    value={editableTweetText}
                    onChange={(e) => setEditableTweetText(e.target.value)}
                    rows={4}
                    maxLength={280}
                    className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                    placeholder="ツイート内容を編集..."
                  />
                  <div className="flex justify-between items-center mt-1">
                    <span className="text-xs text-gray-500">
                      {editableTweetText?.length || 0}/280文字
                    </span>
                    {(editableTweetText?.length || 0) > 280 && (
                      <span className="text-xs text-red-500 font-medium">
                        文字数制限を超えています
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-xs text-gray-500">
                  <p>リポジトリ: {generatedTweet.repository}</p>
                  <p>コミットメッセージ: {generatedTweet.commit_message}</p>
                </div>
              </div>
            )}

            {/* 投稿結果表示 */}
            {postResult && (
              <div className={`p-4 border rounded-md ${
                postResult.success
                  ? 'bg-green-50 border-green-200'
                  : 'bg-red-50 border-red-200'
              }`}>
                <p className={`font-medium ${
                  postResult.success ? 'text-green-800' : 'text-red-800'
                }`}>
                  {postResult.success ? '投稿成功!' : '投稿失敗'}
                </p>
                <p className={`text-sm mt-1 ${
                  postResult.success ? 'text-green-700' : 'text-red-700'
                }`}>
                  {postResult.message}
                </p>
                {postResult.tweet_id && (
                  <p className="text-xs text-green-600 mt-1">
                    Tweet ID: {postResult.tweet_id}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  )
} 