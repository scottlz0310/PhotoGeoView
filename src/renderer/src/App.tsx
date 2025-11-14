import { useState } from 'react'

function App(): JSX.Element {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 bg-white dark:bg-gray-900">
      <header className="mb-12 text-center">
        <h1 className="text-5xl font-bold bg-gradient-to-br from-purple-600 to-purple-900 bg-clip-text text-transparent mb-4">
          PhotoGeoView
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-400">
          Modern Photo Geo-Tagging Application
        </p>
      </header>

      <main className="w-full max-w-4xl">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-8 shadow-lg">
          <h2 className="text-3xl font-semibold text-gray-900 dark:text-white mb-6">
            Welcome to PhotoGeoView 2.0
          </h2>
          <p className="text-gray-700 dark:text-gray-300 mb-4">Built with:</p>
          <ul className="space-y-2 mb-8 text-gray-800 dark:text-gray-200">
            <li className="text-lg">⚡ Electron {process.versions.electron}</li>
            <li className="text-lg">⚛️ React 19</li>
            <li className="text-lg">🔷 TypeScript 5.7+</li>
            <li className="text-lg">🚀 Vite 6</li>
            <li className="text-lg">🎨 TailwindCSS v4</li>
          </ul>

          <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-6 mb-6">
            <button
              type="button"
              onClick={() => setCount((count) => count + 1)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-md font-medium transition-colors"
            >
              Count is {count}
            </button>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-4">
              Click the button to test React state
            </p>
          </div>

          <p className="text-lg bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100 rounded-lg p-4 text-center">
            ✨ Ready for AI-driven development with TypeScript
          </p>
        </div>
      </main>

      <footer className="mt-12 text-sm text-gray-500 dark:text-gray-400">
        <p>🤖 Generated with Claude Code | Built with modern tech stack</p>
      </footer>
    </div>
  )
}

export default App
