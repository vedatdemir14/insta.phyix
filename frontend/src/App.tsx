import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { Layout } from 'antd';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Scraper from './pages/Scraper';
import Messages from './pages/Messages';
import Analytics from './pages/Analytics';
import Users from './pages/Users';
import './App.css';

const { Content } = Layout;

const App: React.FC = () => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#667eea',
          borderRadius: 8,
        },
      }}
    >
      <Router>
        <Layout style={{ minHeight: '100vh' }}>
          <Sidebar />
          <Layout>
            <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', borderRadius: 8 }}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/scraper" element={<Scraper />} />
                <Route path="/messages" element={<Messages />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/users" element={<Users />} />
              </Routes>
            </Content>
          </Layout>
        </Layout>
      </Router>
    </ConfigProvider>
  );
};

export default App;