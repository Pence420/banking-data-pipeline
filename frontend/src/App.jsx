import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer
} from 'recharts';
import './App.css';

const API_URL = 'http://localhost:8000/api';

function App() {
  const [metrics, setMetrics] = useState({});
  const [customers, setCustomers] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [metricsRes, customersRes, accountsRes, transactionsRes] = await Promise.all([
        axios.get(`${API_URL}/metrics`),
        axios.get(`${API_URL}/customers`),
        axios.get(`${API_URL}/accounts`),
        axios.get(`${API_URL}/transactions`)
      ]);

      setMetrics(metricsRes.data);
      setCustomers(customersRes.data);
      setAccounts(accountsRes.data);
      setTransactions(transactionsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <h1>🏦 Loading Banking Dashboard...</h1>
      </div>
    );
  }

  // Prepare chart data
  const loyaltyData = customers.reduce((acc, c) => {
    const tier = c.loyalty_tier || 'Unknown';
    acc[tier] = (acc[tier] || 0) + 1;
    return acc;
  }, {});

  const loyaltyChart = Object.keys(loyaltyData).map(key => ({
    name: key,
    value: loyaltyData[key]
  }));

  const statusData = customers.reduce((acc, c) => {
    const status = c.status || 'Unknown';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});

  const statusChart = Object.keys(statusData).map(key => ({
    name: key,
    value: statusData[key]
  }));

  const COLORS = ['#FFD700', '#C0C0C0', '#CD7F32', '#3498db', '#2ecc71'];

  return (
    <div className="dashboard">
      <header>
        <h1>🏦 Banking Data Pipeline Dashboard</h1>
        <p>Real-time analytics dari Supabase CDC + DuckDB</p>
      </header>

      <div className="metrics-grid">
        <div className="metric-card">
          <h3>👥 Total Customers</h3>
          <h1>{metrics.total_customers?.toLocaleString() || 0}</h1>
        </div>
        <div className="metric-card">
          <h3>🏦 Total Accounts</h3>
          <h1>{metrics.total_accounts?.toLocaleString() || 0}</h1>
        </div>
        <div className="metric-card">
          <h3>💳 Total Transactions</h3>
          <h1>{metrics.total_transactions?.toLocaleString() || 0}</h1>
        </div>
        <div className="metric-card">
          <h3>💰 Total Volume</h3>
          <h1>Rp {(metrics.total_volume || 0).toLocaleString()}</h1>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3>Loyalty Tier Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={loyaltyChart}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {loyaltyChart.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Customer Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={statusChart}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3498db" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="data-table">
        <h2>📋 Recent Transactions</h2>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {transactions.slice(0, 20).map(t => (
                <tr key={t.transaction_id}>
                  <td>{t.transaction_id}</td>
                  <td>{t.transaction_type}</td>
                  <td>Rp {(t.amount || 0).toLocaleString()}</td>
                  <td>
                    <span className={`status-badge ${t.transaction_status}`}>
                      {t.transaction_status}
                    </span>
                  </td>
                  <td>{new Date(t.transaction_date).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <footer>
        <p>Built with ❤️ using Supabase + DuckDB + React</p>
      </footer>
    </div>
  );
}

export default App;