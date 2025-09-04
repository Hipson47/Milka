import React from 'react';
import { InpaintingWorkflow } from './components/InpaintingWorkflow';
import { Header } from './components/Header';

function App() {
  return (
    <div className="min-h-screen">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <InpaintingWorkflow />
      </main>
    </div>
  );
}

export default App;
