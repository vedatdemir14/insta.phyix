import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Sidebar from './components/Sidebar';
import Campaigns from './pages/Campaigns';
import Accounts from './pages/Accounts';
import Leads from './pages/Leads';
import Login from './pages/Login';

const { Content } = Layout;

const AppContent: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Layout style={{ minHeight: '100vh', background: '#ffffff' }}>
      {isAuthenticated && <Sidebar />}
      <Layout style={{ background: '#ffffff' }}>
        <Content style={{ 
          margin: 0, 
          padding: 0, 
          background: '#ffffff', 
          color: '#000000',
          minHeight: '100vh'
        }}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Navigate to="/campaigns" replace />} />
            <Route path="/campaigns" element={<ProtectedRoute><Campaigns /></ProtectedRoute>} />
            <Route path="/accounts" element={<ProtectedRoute><Accounts /></ProtectedRoute>} />
            <Route path="/leads" element={<ProtectedRoute><Leads /></ProtectedRoute>} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

const App: React.FC = () => {
  console.log('🔧 App component rendering...');
  
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
};

export default App;