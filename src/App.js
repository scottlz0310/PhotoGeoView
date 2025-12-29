import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
function App() {
    const [greeting, setGreeting] = useState('');
    async function greet() {
        try {
            const result = await invoke('greet', { name: 'PhotoGeoView' });
            setGreeting(result);
        }
        catch (error) {
            console.error('Failed to invoke command:', error);
            setGreeting('Error: Failed to invoke command');
        }
    }
    return (_jsxs("div", { className: "container", children: [_jsx("h1", { children: "PhotoGeoView v3.0.0" }), _jsx("p", { children: "Tauri + React + TypeScript" }), _jsxs("div", { className: "card", children: [_jsx("button", { type: "button", onClick: () => void greet(), children: "Greet" }), greeting && _jsx("p", { children: greeting })] }), _jsx("p", { className: "info", children: "\uD83D\uDCCD \u5199\u771F\u306B\u57CB\u3081\u8FBC\u307E\u308C\u305F\u4F4D\u7F6E\u60C5\u5831\u3092\u5730\u56F3\u4E0A\u306B\u898B\u3048\u308B\u5316" })] }));
}
export default App;
