import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Typography, Spin } from 'antd';
import { UserOutlined, MessageOutlined, SearchOutlined, BarChartOutlined } from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiService } from '../services/api';

const { Title } = Typography;

interface DashboardStats {
  total_users: number;
  total_messages: number;
  total_scrapes: number;
  success_rate: number;
  daily_stats: Array<{
    date: string;
    users: number;
    messages: number;
    scrapes: number;
  }>;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      setLoading(true);
      const response = await apiService.getDashboardStats();
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>Dashboard</Title>
      
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="card-hover">
            <Statistic
              title="Total Users"
              value={stats?.total_users || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#667eea' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="card-hover">
            <Statistic
              title="Messages Sent"
              value={stats?.total_messages || 0}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="card-hover">
            <Statistic
              title="Scrapes Completed"
              value={stats?.total_scrapes || 0}
              prefix={<SearchOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="card-hover">
            <Statistic
              title="Success Rate"
              value={stats?.success_rate || 0}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Daily Activity" className="card-hover">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={stats?.daily_stats || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="users" stroke="#667eea" strokeWidth={2} />
                <Line type="monotone" dataKey="messages" stroke="#52c41a" strokeWidth={2} />
                <Line type="monotone" dataKey="scrapes" stroke="#fa8c16" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Recent Activity" className="card-hover">
            <div style={{ padding: '20px 0' }}>
              <p>📊 Last scrape: 2 hours ago</p>
              <p>💬 Last message: 1 hour ago</p>
              <p>👤 New user added: 3 hours ago</p>
              <p>📈 Analytics updated: 4 hours ago</p>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
