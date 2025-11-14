import { useState } from 'react'

function App(): JSX.Element {
  const [count, setCount] = useState(0)

  return (
    <div className="app">
      <header className="app-header">
        <h1>PhotoGeoView</h1>
        <p className="subtitle">Modern Photo Geo-Tagging Application</p>
      </header>

      <main className="app-main">
        <div className="card">
          <h2>Welcome to PhotoGeoView 2.0</h2>
          <p>Built with:</p>
          <ul className="tech-stack">
            <li>⚡ Electron {process.versions.electron}</li>
            <li>⚛️ React 19</li>
            <li>🔷 TypeScript 5.7+</li>
            <li>🚀 Vite 6</li>
            <li>🎨 Modern UI Framework</li>
          </ul>

          <div className="demo">
            <button type="button" onClick={() => setCount((count) => count + 1)}>
              Count is {count}
            </button>
            <p className="note">Click the button to test React state</p>
          </div>

          <p className="status">
            ✨ Ready for AI-driven development with TypeScript
          </p>
        </div>
      </main>

      <footer className="app-footer">
        <p>
          🤖 Generated with Claude Code | Built with modern tech stack
        </p>
      </footer>
    </div>
  )
}

export default App
