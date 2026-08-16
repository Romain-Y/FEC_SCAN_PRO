import { useState } from 'react'
import './App.css'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import Login from './Login'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('accessToken'))

  const [file, setFile] = useState(null)
  const [nomClient, setNomClient] = useState('')
  const [sirenClient, setSirenClient] = useState('')
  const [status, setStatus] = useState('idle') 
  const [errorMessage, setErrorMessage] = useState('')
  const [results, setResults] = useState(null) 

  const [activeTab, setActiveTab] = useState('upload')
  const [historyList, setHistoryList] = useState([])

  const [filter, setFilter] = useState('ALL')
  const [currentPage, setCurrentPage] = useState(1)
  const rowsPerPage = 50

  const handleLogout = () => {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    setIsAuthenticated(false)
    setResults(null)        // Remet à zéro l'analyse courante
    setHistoryList([])
  }

  if (!isAuthenticated) {
    return <Login onLoginSuccess={() => setIsAuthenticated(true)} />
  }

  const handleFileChange = (event) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0])
      setStatus('idle')
      setResults(null)
    }
  }

  const handleUpload = () => {
    if (!file) {
      setStatus('error')
      setErrorMessage("Veuillez sélectionner un fichier FEC à analyser.")
      return
    }

    setStatus('loading')
    const formData = new FormData()
    formData.append('fichier_fec', file)
    formData.append('nom_client', nomClient || "Client par défaut")
    formData.append('siren', sirenClient || "000000000")

    const token = localStorage.getItem('accessToken')

    fetch('http://127.0.0.1:8000/api/upload/', {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: formData,
    })
      .then(response => {
        if (!response.ok) throw new Error(`Erreur serveur (${response.status})`)
        return response.json()
      })
      .then(data => {
        if (data && data.anomalies) {
          setStatus('success')
          setResults(data)
          setFilter('ALL')
          setCurrentPage(1)
        } else {
          setStatus('error')
          setErrorMessage(data.error || "Réponse invalide du serveur.")
        }
      })
      .catch((err) => {
        console.error(err)
        setStatus('error')
        setErrorMessage(err.message)
      })
  }

  const handleReset = () => {
    setFile(null)
    setNomClient('')
    setSirenClient('')
    setStatus('idle')
    setResults(null)
    setErrorMessage('')
  }

  const fetchHistory = () => {
    const token = localStorage.getItem('accessToken')
    fetch('http://127.0.0.1:8000/api/historique/', {
      headers: { 'Authorization': token ? `Bearer ${token}` : '' }
    })
      .then(res => res.json())
      .then(data => setHistoryList(data))
      .catch(err => console.error("Erreur historique", err))
  }

  const handleTabChange = (tab) => {
    setActiveTab(tab)
    if (tab === 'history') fetchHistory()
  }

  const handleExportExcel = () => {
    fetch('http://127.0.0.1:8000/api/export/excel/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(results),
    })
    .then(res => res.blob())
    .then(blob => {
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'Rapport_Audit_FEC.xlsx'
      a.click()
    })
    .catch(err => alert(`Erreur export : ${err.message}`))
  }

  const handleExportPdf = () => {
    fetch('http://127.0.0.1:8000/api/export/pdf/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(results),
    })
    .then(res => res.blob())
    .then(blob => {
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'Rapport_Audit_FEC.pdf'
      a.click()
    })
    .catch(err => alert(`Erreur export PDF : ${err.message}`))
  }

  const getChartData = () => {
    if (!results || !results.anomalies) return []
    let critiques = 0, hautes = 0, moyens = 0
    results.anomalies.forEach(ano => {
      const gravite = ano.Gravité?.toUpperCase() || ''
      if (gravite.includes('CRITIQUE')) critiques++
      else if (gravite.includes('HAUTE') || gravite.includes('ÉLEVÉ') || gravite.includes('ELEVE')) hautes++
      else if (gravite.includes('MOYEN')) moyens++
    })
    return [
      { name: 'Critiques', value: critiques, color: '#dc2626' },
      { name: 'Hautes', value: hautes, color: '#ea580c' },
      { name: 'Moyens', value: moyens, color: '#d97706' },
    ].filter(item => item.value > 0)
  }

  const filteredAnomalies = results?.anomalies.filter(ano => {
    if (filter === 'ALL') return true
    const gravite = ano.Gravité?.toUpperCase() || ''
    if (filter === 'CRITIQUE') return gravite.includes('CRITIQUE')
    if (filter === 'ELEVE') return gravite.includes('HAUTE') || gravite.includes('ÉLEVÉ') || gravite.includes('ELEVE')
    if (filter === 'MOYEN') return gravite.includes('MOYEN')
    return true
  }) || []

  const totalPages = Math.max(1, Math.ceil(filteredAnomalies.length / rowsPerPage))
  const currentAnomalies = filteredAnomalies.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage)

  return (
    <div style={{ backgroundColor: '#f8fafc', minHeight: '100vh', fontFamily: "'Inter', system-ui, -apple-system, sans-serif", color: '#0f172a' }}>
      
      {/* NAVBAR */}
      <header style={{ backgroundColor: '#ffffff', borderBottom: '1px solid #e2e8f0', padding: '16px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ backgroundColor: '#0f172a', color: '#ffffff', width: '36px', height: '36px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>FEC</div>
          <h1 style={{ fontSize: '18px', fontWeight: '600', margin: 0 }}>Audit Compta Engine</h1>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button 
            onClick={() => handleTabChange('upload')}
            style={{ padding: '8px 16px', borderRadius: '6px', fontSize: '14px', fontWeight: '500', border: 'none', cursor: 'pointer', backgroundColor: activeTab === 'upload' ? '#0f172a' : 'transparent', color: activeTab === 'upload' ? '#ffffff' : '#64748b' }}
          >
            Analyse
          </button>
          <button 
            onClick={() => handleTabChange('history')}
            style={{ padding: '8px 16px', borderRadius: '6px', fontSize: '14px', fontWeight: '500', border: 'none', cursor: 'pointer', backgroundColor: activeTab === 'history' ? '#0f172a' : 'transparent', color: activeTab === 'history' ? '#ffffff' : '#64748b' }}
          >
            Historique Cabinet
          </button>
          <button 
            onClick={handleLogout} 
            style={{ padding: '8px 16px', borderRadius: '6px', fontSize: '14px', fontWeight: '500', border: '1px solid #e2e8f0', backgroundColor: '#ffffff', color: '#dc2626', cursor: 'pointer', marginLeft: '12px' }}
          >
            Déconnexion
          </button>
        </div>
      </header>

      <main style={{ maxWidth: '1200px', margin: '32px auto', padding: '0 24px' }}>
        
        {/* ONGLET 1 : IMPORT / FORMULAIRE */}
        {activeTab === 'upload' && status !== 'success' && (
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
            
            <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '4px' }}>Nouvelle analyse de dossier</h2>
              <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '24px' }}>Renseignez le dossier client et importez le fichier FEC (.txt, .csv).</p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '500', color: '#475569', marginBottom: '6px' }}>Nom du client</label>
                  <input 
                    type="text" 
                    placeholder="ex: Acme Corp" 
                    value={nomClient} 
                    onChange={(e) => setNomClient(e.target.value)}
                    style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '500', color: '#475569', marginBottom: '6px' }}>Numéro SIREN</label>
                  <input 
                    type="text" 
                    placeholder="9 chiffres" 
                    maxLength={9}
                    value={sirenClient} 
                    onChange={(e) => setSirenClient(e.target.value)}
                    style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', boxSizing: 'border-box' }}
                  />
                </div>
              </div>

              {/* ZONE DROPFILE PRO */}
              <div style={{ border: '2px dashed #cbd5e1', borderRadius: '8px', padding: '32px 16px', textAlign: 'center', backgroundColor: '#f8fafc', cursor: 'pointer', marginBottom: '20px' }}>
                <input 
                  type="file" 
                  accept=".csv, .txt" 
                  onChange={handleFileChange} 
                  id="file-input"
                  style={{ display: 'none' }} 
                />
                <label htmlFor="file-input" style={{ cursor: 'pointer' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>📁</div>
                  <span style={{ fontSize: '14px', fontWeight: '500', color: '#0f172a' }}>
                    {file ? file.name : "Cliquez pour sélectionner le fichier FEC"}
                  </span>
                  <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>Format officiel DGFiP accepté</p>
                </label>
              </div>

              <button 
                onClick={handleUpload} 
                disabled={status === 'loading'}
                style={{ width: '100%', padding: '12px', borderRadius: '6px', border: 'none', backgroundColor: '#0f172a', color: '#ffffff', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}
              >
                {status === 'loading' ? 'Lancement du contrôle...' : 'Lancer le contrôle d\'audit'}
              </button>

              {status === 'error' && (
                <div style={{ marginTop: '16px', padding: '12px', borderRadius: '6px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', fontSize: '13px' }}>
                  {errorMessage}
                </div>
              )}
            </div>

            {/* CARTE INFO REGLES */}
            <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: '#0f172a' }}>Périmètre de contrôle</h3>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '13px', color: '#475569', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <li style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ color: '#dc2626' }}>●</span>
                  <span><strong>Critiques :</strong> Caisse négative (compte 53), attente non soldé (471).</span>
                </li>
                <li style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ color: '#ea580c' }}>●</span>
                  <span><strong>Hautes :</strong> Doublons de pièces, mots-clés interdits, dates hors exercice.</span>
                </li>
                <li style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ color: '#d97706' }}>●</span>
                  <span><strong>Moyennes :</strong> Écritures dominicales, montants ronds suspects.</span>
                </li>
              </ul>
            </div>

          </div>
        )}

        {/* ONGLET 2 : HISTORIQUE */}
        {activeTab === 'history' && (
          <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>Historique des audits enregistrés</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e2e8f0', color: '#64748b' }}>
                  <th style={{ padding: '12px' }}>ID</th>
                  <th style={{ padding: '12px' }}>Client</th>
                  <th style={{ padding: '12px' }}>Fichier</th>
                  <th style={{ padding: '12px' }}>Date</th>
                  <th style={{ padding: '12px' }}>Anomalies</th>
                  <th style={{ padding: '12px' }}>Risque global</th>
                </tr>
              </thead>
              <tbody>
                {historyList.map(item => (
                  <tr key={item.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '12px', fontWeight: '600' }}>#{item.id}</td>
                    <td style={{ padding: '12px' }}>{item.client}</td>
                    <td style={{ padding: '12px', color: '#64748b' }}>{item.fichier}</td>
                    <td style={{ padding: '12px' }}>{new Date(item.date).toLocaleDateString('fr-FR')}</td>
                    <td style={{ padding: '12px', fontWeight: '600', color: '#dc2626' }}>{item.total_anomalies}</td>
                    <td style={{ padding: '12px', fontWeight: '600' }}>{item.montant_risque.toLocaleString('fr-FR')} €</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* VUE 3 : RESULTATS */}
        {activeTab === 'upload' && status === 'success' && results && (
          <div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div>
                <h2 style={{ fontSize: '20px', fontWeight: '600', margin: 0 }}>Synthèse de l'audit</h2>
                <p style={{ fontSize: '14px', color: '#64748b', margin: '4px 0 0 0' }}>Analyse terminée pour {nomClient || 'le dossier'}</p>
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button onClick={handleExportPdf} style={{ padding: '8px 16px', borderRadius: '6px', border: '1px solid #e2e8f0', backgroundColor: '#ffffff', fontSize: '13px', fontWeight: '500', cursor: 'pointer' }}>Export PDF</button>
                <button onClick={handleExportExcel} style={{ padding: '8px 16px', borderRadius: '6px', border: '1px solid #e2e8f0', backgroundColor: '#ffffff', fontSize: '13px', fontWeight: '500', cursor: 'pointer' }}>Export Excel</button>
                <button onClick={handleReset} style={{ padding: '8px 16px', borderRadius: '6px', border: 'none', backgroundColor: '#0f172a', color: '#ffffff', fontSize: '13px', fontWeight: '500', cursor: 'pointer' }}>Nouveau dossier</button>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '24px' }}>
              <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px' }}>
                <span style={{ fontSize: '12px', color: '#64748b', fontWeight: '500' }}>ANOMALIES DÉTECTÉES</span>
                <div style={{ fontSize: '28px', fontWeight: '700', color: '#0f172a', marginTop: '4px' }}>{results.stats.total_anomalies}</div>
              </div>
              <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px' }}>
                <span style={{ fontSize: '12px', color: '#64748b', fontWeight: '500' }}>MONTANT TOTAL EN RISQUE</span>
                <div style={{ fontSize: '28px', fontWeight: '700', color: '#dc2626', marginTop: '4px' }}>{results.stats.montant_risque.toLocaleString('fr-FR')} €</div>
              </div>
              <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '12px 20px', height: '120px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={getChartData()} cx="50%" cy="50%" innerRadius={30} outerRadius={45} dataKey="value">
                      {getChartData().map((entry, index) => <Cell key={index} fill={entry.color} />)}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* TABLEAU ANOMALIES */}
            <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
              
              <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                {['ALL', 'CRITIQUE', 'ELEVE', 'MOYEN'].map(f => (
                  <button 
                    key={f} 
                    onClick={() => { setFilter(f); setCurrentPage(1); }}
                    style={{ padding: '6px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: '500', border: '1px solid #e2e8f0', backgroundColor: filter === f ? '#0f172a' : '#ffffff', color: filter === f ? '#ffffff' : '#64748b', cursor: 'pointer' }}
                  >
                    {f === 'ALL' ? `Tout (${results.anomalies.length})` : f}
                  </button>
                ))}
              </div>

              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #e2e8f0', color: '#64748b' }}>
                    <th style={{ padding: '10px' }}>Gravité</th>
                    <th style={{ padding: '10px' }}>Règle</th>
                    <th style={{ padding: '10px' }}>Date</th>
                    <th style={{ padding: '10px' }}>JRN</th>
                    <th style={{ padding: '10px' }}>Compte</th>
                    <th style={{ padding: '10px' }}>Débit</th>
                    <th style={{ padding: '10px' }}>Crédit</th>
                  </tr>
                </thead>
                <tbody>
                  {currentAnomalies.map((ano, index) => (
                    <tr key={index} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '10px', fontWeight: '600', color: ano.Gravité?.includes('CRITIQUE') ? '#dc2626' : ano.Gravité?.includes('MOYEN') ? '#d97706' : '#ea580c' }}>{ano.Gravité}</td>
                      <td style={{ padding: '10px', color: '#475569' }}>{ano.Type_Anomalie}</td>
                      <td style={{ padding: '10px', color: '#64748b' }}>{ano.Date ? ano.Date.substring(0, 10) : '-'}</td>
                      <td style={{ padding: '10px' }}>{ano.Journal}</td>
                      <td style={{ padding: '10px', fontWeight: '500' }}>{ano.Compte}</td>
                      <td style={{ padding: '10px', color: '#ea580c' }}>{ano.Debit > 0 ? `${ano.Debit} €` : '-'}</td>
                      <td style={{ padding: '10px', color: '#16a34a' }}>{ano.Credit > 0 ? `${ano.Credit} €` : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* PAGINATION */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', fontSize: '13px', color: '#64748b' }}>
                <button disabled={currentPage === 1} onClick={() => setCurrentPage(p => p - 1)} style={{ padding: '6px 12px', border: '1px solid #e2e8f0', borderRadius: '6px', backgroundColor: '#ffffff', cursor: 'pointer' }}>Précédent</button>
                <span>Page {currentPage} sur {totalPages}</span>
                <button disabled={currentPage === totalPages} onClick={() => setCurrentPage(p => p + 1)} style={{ padding: '6px 12px', border: '1px solid #e2e8f0', borderRadius: '6px', backgroundColor: '#ffffff', cursor: 'pointer' }}>Suivant</button>
              </div>

            </div>

          </div>
        )}

      </main>
    </div>
  )
}

export default App