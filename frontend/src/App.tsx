import { Link, Routes, Route } from 'react-router-dom';
import { useCounterStore } from './stores/counter';
import Home from './pages/Home';
import About from './pages/About';

export default function App() {
  const count = useCounterStore((s) => s.count);
  const increment = useCounterStore((s) => s.increment);
  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: 24 }}>
      <h1>Loanpedia Frontend</h1>
      <nav style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Link to="/">Home</Link>
        <Link to="/about">About</Link>
      </nav>
      <p>Vite + React + TypeScript + Router + Zustand</p>
      <button onClick={increment}>count: {count}</button>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </div>
  );
}
