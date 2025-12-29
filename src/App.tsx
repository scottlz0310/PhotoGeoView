import { useState } from 'react'
import { invoke } from '@tauri-apps/api/core'

function App(): React.ReactElement {
  const [greeting, setGreeting] = useState<string>('')

  async function greet(): Promise<void> {
    try {
      const result = await invoke<string>('greet', { name: 'PhotoGeoView' })
      setGreeting(result)
    } catch (error) {
      console.error('Failed to invoke command:', error)
      setGreeting('Error: Failed to invoke command')
    }
  }

  return (
    <div className="container">
      <h1>PhotoGeoView v3.0.0</h1>
      <p>Tauri + React + TypeScript</p>

      <div className="card">
        <button type="button" onClick={() => void greet()}>
          Greet
        </button>
        {greeting && <p>{greeting}</p>}
      </div>

      <p className="info">
        📍 写真に埋め込まれた位置情報を地図上に見える化
      </p>
    </div>
  )
}

export default App
