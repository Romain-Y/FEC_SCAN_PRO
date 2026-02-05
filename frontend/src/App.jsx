import { useEffect, useState } from 'react'

function App() {
  const [message, setMessage] = useState('En attente du serveur...')

  useEffect(() => {
    // On appelle l'API Django
    fetch('http://127.0.0.1:8000/api/test/')
      .then(response => response.json())
      .then(data => setMessage(data.message))
      .catch(error => setMessage("❌ Erreur de connexion avec Django"));
  }, [])

  return (
    <div style={{ textAlign: 'center', marginTop: '50px', fontFamily: 'Arial' }}>
      <h1>Test d'Architecture</h1>
      <div style={{ 
        padding: '20px', 
        border: '2px solid #333', 
        display: 'inline-block',
        borderRadius: '10px',
        backgroundColor: '#f0f0f0'
      }}>
        <h3>Message reçu du Backend :</h3>
        <p style={{ color: 'green', fontWeight: 'bold', fontSize: '18px' }}>
          {message}
        </p>
      </div>
    </div>
  )
}

export default App