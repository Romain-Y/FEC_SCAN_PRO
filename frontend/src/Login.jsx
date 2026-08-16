import { useState } from 'react'

function Login({ onLoginSuccess }) {
  const [isRegistering, setIsRegistering] = useState(false)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [successMsg, setSuccessMsg] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleLogin = (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')
    setSuccessMsg('')

    fetch('http://127.0.0.1:8000/api/token/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Identifiants ou mot de passe invalides.')
        return res.json()
      })
      .then((data) => {
        localStorage.setItem('accessToken', data.access)
        localStorage.setItem('refreshToken', data.refresh)
        onLoginSuccess()
      })
      .catch((err) => setError(err.message))
      .finally(() => setIsLoading(false))
  }

  const handleRegister = (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')
    setSuccessMsg('')

    if (password !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas.')
      setIsLoading(false)
      return
    }

    if (password.length < 8) {
      setError('Le mot de passe doit contenir au moins 8 caractères.')
      setIsLoading(false)
      return
    }

    fetch('http://127.0.0.1:8000/api/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    })
      .then(async (res) => {
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Erreur lors de la création du compte.')
        return data
      })
      .then(() => {
        setSuccessMsg('Compte créé avec succès ! Vous pouvez maintenant vous connecter.')
        setIsRegistering(false)
        setPassword('')
        setConfirmPassword('')
      })
      .catch((err) => setError(err.message))
      .finally(() => setIsLoading(false))
  }

  return (
    <div style={{ 
      backgroundColor: '#f8fafc', 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
      color: '#0f172a'
    }}>
      <div style={{ 
        width: '100%', 
        maxWidth: '400px', 
        backgroundColor: '#ffffff', 
        border: '1px solid #e2e8f0', 
        borderRadius: '12px', 
        padding: '32px',
        boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)'
      }}>
        
        {/* HEADER */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{ 
            backgroundColor: '#0f172a', 
            color: '#ffffff', 
            width: '44px', 
            height: '44px', 
            borderRadius: '10px', 
            display: 'inline-flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            fontWeight: 'bold',
            fontSize: '16px',
            marginBottom: '12px'
          }}>
            FEC
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: '600', margin: '0 0 6px 0', color: '#0f172a' }}>
            Audit Compta Engine
          </h2>
          <p style={{ fontSize: '13px', color: '#64748b', margin: 0 }}>
            {isRegistering ? 'Création de votre compte comptable' : 'Espace d\'accès sécurisé du cabinet'}
          </p>
        </div>

        {/* NOTIFICATIONS */}
        {error && (
          <div style={{ marginBottom: '16px', padding: '10px 14px', borderRadius: '6px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', fontSize: '13px' }}>
            {error}
          </div>
        )}

        {successMsg && (
          <div style={{ marginBottom: '16px', padding: '10px 14px', borderRadius: '6px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534', fontSize: '13px' }}>
            {successMsg}
          </div>
        )}

        {/* FORMULAIRE */}
        <form onSubmit={isRegistering ? handleRegister : handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '500', color: '#475569', marginBottom: '6px' }}>Identifiant</label>
            <input 
              type="text" 
              placeholder="ex: c.dupont" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)}
              required
              style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', boxSizing: 'border-box' }}
            />
          </div>

          {isRegistering && (
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '500', color: '#475569', marginBottom: '6px' }}>Adresse Email (optionnelle)</label>
              <input 
                type="email" 
                placeholder="comptable@cabinet.fr" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)}
                style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', boxSizing: 'border-box' }}
              />
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '500', color: '#475569', marginBottom: '6px' }}>Mot de passe</label>
            <input 
              type="password" 
              placeholder="••••••••" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', boxSizing: 'border-box' }}
            />
          </div>

          {isRegistering && (
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '500', color: '#475569', marginBottom: '6px' }}>Confirmer le mot de passe</label>
              <input 
                type="password" 
                placeholder="••••••••" 
                value={confirmPassword} 
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', boxSizing: 'border-box' }}
              />
            </div>
          )}

          <button 
            type="submit" 
            disabled={isLoading}
            style={{ marginTop: '6px', width: '100%', padding: '11px', borderRadius: '6px', border: 'none', backgroundColor: '#0f172a', color: '#ffffff', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}
          >
            {isLoading ? 'Chargement...' : isRegistering ? 'Créer mon compte' : 'Se connecter'}
          </button>
        </form>

        {/* BASCULE CONNEXION / INSCRIPTION */}
        <div style={{ textAlign: 'center', marginTop: '20px', paddingTop: '16px', borderTop: '1px solid #f1f5f9' }}>
          <button 
            onClick={() => {
              setIsRegistering(!isRegistering)
              setError('')
              setSuccessMsg('')
            }}
            style={{ background: 'none', border: 'none', color: '#2563eb', fontSize: '13px', cursor: 'pointer', fontWeight: '500' }}
          >
            {isRegistering ? 'Déjà un compte ? Se connecter' : 'Première connexion ? Créer un compte'}
          </button>
        </div>

      </div>
    </div>
  )
}

export default Login