/** @type {import('next').NextConfig} */

const nextConfig = {
  // 環境変数をクライアントサイドで利用可能にする
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig 