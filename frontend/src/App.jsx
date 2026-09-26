import { useCallback, useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import './App.css'

const API_URL = 'http://localhost:8000/api'
const LOYALTY_COLORS = ['#d7ff75', '#c7c8c2', '#9a7452', '#f3f0e7']
const formatNumber = (value = 0) => new Intl.NumberFormat('id-ID').format(value)
const formatCurrency = (value = 0, compact = false) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0, notation: compact ? 'compact' : 'standard' }).format(value)

function Mark({ name, className = '' }) {
  const paths = {
    customers: 'M5 16c0-3 2-5 5-5s5 2 5 5M10 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm6 2c2.5 0 4 1.7 4 4.5M16 9a2.5 2.5 0 1 0-1-4.8',
    accounts: 'M3 9h18M5 9v8m4-8v8m6-8v8m4-8v8M3 20h18M12 3 3 7h18l-9-4Z',
    transactions: 'm7 7-4 4 4 4m-4-4h14m0-4 4 4-4 4',
    volume: 'M12 3v18m5-14.5c-1-1-2.6-1.5-5-1.5-3 0-5 1.4-5 3.5 0 5 10 2.5 10 7.5 0 2.1-2 3.5-5 3.5-2.4 0-4-.5-5-1.5',
    refresh: 'M20 6v5h-5M4 18v-5h5m10.3-2A8 8 0 0 0 6.2 6.2L4 8m16 8-2.2 1.8A8 8 0 0 1 4.7 14',
  }
  return <svg className={className} viewBox="0 0 24 24" aria-hidden="true"><path d={paths[name]} /></svg>
}

function MetricCard({ label, value, detail, icon, featured = false }) {
  return <article className={`metric-shell ${featured ? 'metric-shell--featured' : ''}`}><div className="metric-core"><div className="metric-heading"><span>{label}</span><Mark name={icon} /></div><strong>{value}</strong><p>{detail}</p></div></article>
}

function App() {
  const [metrics, setMetrics] = useState({})
  const [customers, setCustomers] = useState([])
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [lastSync, setLastSync] = useState(null)

  const fetchData = useCallback(async () => {
    try {
      const [metricsRes, customersRes, transactionsRes] = await Promise.all([
        axios.get(`${API_URL}/metrics`), axios.get(`${API_URL}/customers`), axios.get(`${API_URL}/transactions`),
      ])
      setMetrics(metricsRes.data)
      setCustomers(customersRes.data)
      setTransactions(transactionsRes.data)
      setLastSync(new Date())
      setError(false)
    } catch (requestError) {
      console.error('Banking data request failed:', requestError)
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const initialRequest = window.setTimeout(fetchData, 0)
    const interval = window.setInterval(fetchData, 30000)
    return () => {
      window.clearTimeout(initialRequest)
      window.clearInterval(interval)
    }
  }, [fetchData])

  const loyaltyChart = useMemo(() => Object.entries(customers.reduce((acc, customer) => {
    const tier = customer.loyalty_tier || 'Unclassified'
    acc[tier] = (acc[tier] || 0) + 1
    return acc
  }, {})).map(([name, value]) => ({ name, value })), [customers])

  const statusChart = useMemo(() => Object.entries(customers.reduce((acc, customer) => {
    const status = customer.status || 'Unknown'
    acc[status] = (acc[status] || 0) + 1
    return acc
  }, {})).map(([name, value]) => ({ name, value })), [customers])

  const flowChart = useMemo(() => transactions.slice(0, 18).reverse().map((transaction, index) => ({ name: String(index + 1).padStart(2, '0'), volume: Number(transaction.amount || 0) })), [transactions])

  if (loading) return <main className="loading-state"><div className="loading-mark" /><p>Connecting analytical layers</p></main>

  return (
    <main className="dashboard">
      <nav className="topbar" aria-label="Dashboard navigation">
        <a className="brand" href="#overview" aria-label="Ledger dashboard home"><span className="brand-mark">L</span><span>LEDGER / 05</span></a>
        <div className="topbar-center"><a href="#overview">Overview</a><a href="#activity">Activity</a><a href="#pipeline">Pipeline</a></div>
        <div className="live-indicator"><span /> CDC live</div>
      </nav>

      <header className="hero" id="overview">
        <div><p className="eyebrow">Banking intelligence / Operational view</p><h1>Money in motion,<br /><em>made legible.</em></h1></div>
        <div className="hero-note"><p>Source changes travel through governed Bronze, Silver, and Gold layers before they reach this decision surface.</p><dl><div><dt>Warehouse</dt><dd>DuckDB</dd></div><div><dt>Change data</dt><dd>Supabase CDC</dd></div><div><dt>Last sync</dt><dd>{lastSync ? lastSync.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) : '—'}</dd></div></dl></div>
      </header>

      {error && <div className="error-banner" role="alert"><span>The local API is unavailable. Start the backend to restore live metrics.</span><button onClick={fetchData}>Retry connection</button></div>}

      <section className="metrics-grid" aria-label="Portfolio metrics">
        <MetricCard label="Customers" value={formatNumber(metrics.total_customers)} detail="profiles in the analytical layer" icon="customers" />
        <MetricCard label="Active accounts" value={formatNumber(metrics.total_accounts)} detail="current SCD records" icon="accounts" />
        <MetricCard label="Transactions" value={formatNumber(metrics.total_transactions)} detail="events processed" icon="transactions" />
        <MetricCard label="Processed volume" value={formatCurrency(metrics.total_volume, true)} detail={formatCurrency(metrics.total_volume)} icon="volume" featured />
      </section>

      <section className="workspace" id="activity">
        <article className="panel panel--flow"><div className="panel-heading"><div><p className="kicker">Transaction pulse</p><h2>Processed volume</h2></div><span>Latest 18 events</span></div><div className="chart chart--flow"><ResponsiveContainer width="100%" height="100%"><AreaChart data={flowChart} margin={{ top: 18, right: 0, bottom: 0, left: 0 }}><defs><linearGradient id="volumeFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#d7ff75" stopOpacity={0.34} /><stop offset="100%" stopColor="#d7ff75" stopOpacity={0} /></linearGradient></defs><CartesianGrid vertical={false} stroke="rgba(255,255,255,.055)" /><XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#72766d', fontSize: 10 }} /><YAxis hide /><Tooltip contentStyle={{ background: '#171a16', border: '1px solid rgba(255,255,255,.1)', borderRadius: 12 }} formatter={(value) => formatCurrency(value, true)} /><Area type="monotone" dataKey="volume" stroke="#d7ff75" strokeWidth={2} fill="url(#volumeFill)" /></AreaChart></ResponsiveContainer></div></article>

        <article className="panel panel--loyalty"><div className="panel-heading"><div><p className="kicker">Customer mix</p><h2>Loyalty distribution</h2></div></div><div className="loyalty-layout"><div className="donut"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={loyaltyChart} dataKey="value" innerRadius="68%" outerRadius="94%" paddingAngle={3} stroke="none">{loyaltyChart.map((entry, index) => <Cell key={entry.name} fill={LOYALTY_COLORS[index % LOYALTY_COLORS.length]} />)}</Pie><Tooltip contentStyle={{ background: '#171a16', border: '1px solid rgba(255,255,255,.1)', borderRadius: 12 }} /></PieChart></ResponsiveContainer><div><strong>{formatNumber(customers.length)}</strong><span>customers</span></div></div><ul>{loyaltyChart.map((entry, index) => <li key={entry.name}><span style={{ background: LOYALTY_COLORS[index % LOYALTY_COLORS.length] }} /><p>{entry.name}</p><strong>{entry.value}</strong></li>)}</ul></div></article>

        <article className="panel panel--status"><div className="panel-heading"><div><p className="kicker">Account health</p><h2>Customer status</h2></div><span>{statusChart.length} states</span></div><div className="chart chart--status"><ResponsiveContainer width="100%" height="100%"><BarChart data={statusChart} layout="vertical" margin={{ top: 8, right: 8, bottom: 0, left: 0 }}><XAxis type="number" hide /><YAxis type="category" dataKey="name" width={74} axisLine={false} tickLine={false} tick={{ fill: '#9a9d94', fontSize: 11 }} /><Tooltip cursor={{ fill: 'rgba(255,255,255,.025)' }} contentStyle={{ background: '#171a16', border: '1px solid rgba(255,255,255,.1)', borderRadius: 12 }} /><Bar dataKey="value" fill="#f3f0e7" radius={[0, 6, 6, 0]} barSize={14} /></BarChart></ResponsiveContainer></div></article>

        <article className="panel panel--pipeline" id="pipeline"><div className="panel-heading"><div><p className="kicker">Data lineage</p><h2>Pipeline state</h2></div><Mark name="refresh" className="refresh-icon" /></div><ol className="pipeline-list"><li><span>01</span><div><strong>Bronze</strong><p>Immutable CDC snapshots</p></div><i>Ready</i></li><li><span>02</span><div><strong>Silver</strong><p>Typed and quality checked</p></div><i>Ready</i></li><li><span>03</span><div><strong>Gold</strong><p>Decision-ready marts</p></div><i>Live</i></li></ol></article>
      </section>

      <section className="activity" aria-labelledby="activity-title"><div className="activity-heading"><div><p className="kicker">Event stream</p><h2 id="activity-title">Recent transactions</h2></div><p>Latest warehouse records, reconciled from the operational source.</p></div><div className="table-wrap"><table><thead><tr><th>Transaction</th><th>Type</th><th>Amount</th><th>Status</th><th>Recorded</th></tr></thead><tbody>{transactions.slice(0, 8).map((transaction) => <tr key={transaction.transaction_id}><td><span className="transaction-id">{transaction.transaction_id}</span></td><td>{transaction.transaction_type || 'Transfer'}</td><td>{formatCurrency(transaction.amount)}</td><td><span className={`status status--${transaction.transaction_status}`}>{transaction.transaction_status || 'recorded'}</span></td><td>{transaction.transaction_date ? new Date(transaction.transaction_date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}</td></tr>)}</tbody></table></div></section>

      <footer><span>Ledger / 05</span><p>Supabase CDC → DuckDB → analytical product</p><span>Jakarta · 2026</span></footer>
    </main>
  )
}

export default App
