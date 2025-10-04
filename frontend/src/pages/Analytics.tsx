import React, { useState, useEffect } from 'react';
import { Card, Input, Button, Select, Typography, Row, Col, Spin, message } from 'antd';
import { SearchOutlined, BarChartOutlined } from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { apiService } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

const Analytics: React.FC = () => {
  const [username, setUsername] = useState('');
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchAnalytics = async () => {
    if (!username.trim()) {
      message.warning('Please enter a username');
      return;
    }

    try {
      setLoading(true);
      const response = await apiService.getAnalytics(username);
      setAnalyticsData(response.data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];

  return (
    <div>
      <Title level={2}>Analytics</Title>
      <Text type="secondary">Analyze Instagram user data and engagement</Text>
      
      <Card style={{ marginTop: 24 }} className="card-hover">
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Input
              placeholder="Enter Instagram username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onPressEnter={fetchAnalytics}
              prefix={<SearchOutlined />}
              size="large"
            />
          </Col>
          <Col>
            <Button
              type="primary"
              onClick={fetchAnalytics}
              loading={loading}
              size="large"
              icon={<BarChartOutlined />}
            >
              Analyze
            </Button>
          </Col>
        </Row>
      </Card>

      {loading && (
        <div className="loading-container">
          <Spin size="large" />
        </div>
      )}

      {analyticsData && (
        <div style={{ marginTop: 24 }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Engagement Over Time" className="card-hover">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={analyticsData.engagement_timeline || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="likes" stroke="#667eea" strokeWidth={2} />
                    <Line type="monotone" dataKey="comments" stroke="#52c41a" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            
            <Col xs={24} lg={12}>
              <Card title="Post Types Distribution" className="card-hover">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={analyticsData.post_types || []}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {(analyticsData.post_types || []).map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={24} lg={12}>
              <Card title="Top Performing Posts" className="card-hover">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={analyticsData.top_posts || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="post_id" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="likes" fill="#667eea" />
                    <Bar dataKey="comments" fill="#52c41a" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            
            <Col xs={24} lg={12}>
              <Card title="Engagement Summary" className="card-hover">
                <div style={{ padding: 20 }}>
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <div style={{ textAlign: 'center' }}>
                        <Title level={3} style={{ margin: 0, color: '#667eea' }}>
                          {analyticsData.avg_likes || 0}
                        </Title>
                        <Text type="secondary">Avg Likes</Text>
                      </div>
                    </Col>
                    <Col span={12}>
                      <div style={{ textAlign: 'center' }}>
                        <Title level={3} style={{ margin: 0, color: '#52c41a' }}>
                          {analyticsData.avg_comments || 0}
                        </Title>
                        <Text type="secondary">Avg Comments</Text>
                      </div>
                    </Col>
                    <Col span={12}>
                      <div style={{ textAlign: 'center' }}>
                        <Title level={3} style={{ margin: 0, color: '#fa8c16' }}>
                          {analyticsData.engagement_rate || 0}%
                        </Title>
                        <Text type="secondary">Engagement Rate</Text>
                      </div>
                    </Col>
                    <Col span={12}>
                      <div style={{ textAlign: 'center' }}>
                        <Title level={3} style={{ margin: 0, color: '#f5222d' }}>
                          {analyticsData.total_posts || 0}
                        </Title>
                        <Text type="secondary">Total Posts</Text>
                      </div>
                    </Col>
                  </Row>
                </div>
              </Card>
            </Col>
          </Row>
        </div>
      )}
    </div>
  );
};

export default Analytics;
