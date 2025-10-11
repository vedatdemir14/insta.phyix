import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, Tabs, message, Row, Col } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (values: { username: string; password: string }) => {
    try {
      setLoading(true);
      await login(values.username, values.password);
      message.success('Login successful!');
      navigate('/campaigns');
    } catch (error: any) {
      message.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: { 
    username: string; 
    email: string; 
    password: string; 
    fullName?: string;
    confirmPassword: string;
  }) => {
    if (values.password !== values.confirmPassword) {
      message.error('Passwords do not match!');
      return;
    }

    try {
      setLoading(true);
      await register(values.username, values.email, values.password, values.fullName);
      message.success('Registration successful!');
      navigate('/campaigns');
    } catch (error: any) {
      message.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <Row justify="center" style={{ width: '100%', maxWidth: '1200px' }}>
        <Col xs={24} sm={20} md={16} lg={12} xl={10}>
          <Card 
            style={{ 
              borderRadius: '16px',
              boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
              border: 'none'
            }}
            bodyStyle={{ padding: '40px' }}
          >
            <div style={{ textAlign: 'center', marginBottom: '32px' }}>
              <Title level={2} className="instagram-gradient" style={{ margin: 0 }}>
                Instagram Scraper
              </Title>
              <Text style={{ color: '#666666', fontSize: '16px' }}>
                Sign in to your account or create a new one
              </Text>
            </div>

            <Tabs defaultActiveKey="login" centered>
              <TabPane tab="Login" key="login">
                <Form
                  name="login"
                  onFinish={handleLogin}
                  layout="vertical"
                  size="large"
                >
                  <Form.Item
                    name="username"
                    rules={[{ required: true, message: 'Please enter your username!' }]}
                  >
                    <Input
                      prefix={<UserOutlined />}
                      placeholder="Username"
                      style={{ borderRadius: '8px' }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="password"
                    rules={[{ required: true, message: 'Please enter your password!' }]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="Password"
                      style={{ borderRadius: '8px' }}
                    />
                  </Form.Item>

                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      style={{
                        width: '100%',
                        height: '48px',
                        borderRadius: '8px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        border: 'none',
                        fontSize: '16px',
                        fontWeight: 'bold'
                      }}
                    >
                      Sign In
                    </Button>
                  </Form.Item>
                </Form>
              </TabPane>

              <TabPane tab="Register" key="register">
                <Form
                  name="register"
                  onFinish={handleRegister}
                  layout="vertical"
                  size="large"
                >
                  <Form.Item
                    name="fullName"
                    rules={[{ required: false }]}
                  >
                    <Input
                      prefix={<UserOutlined />}
                      placeholder="Full Name (Optional)"
                      style={{ borderRadius: '8px' }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="username"
                    rules={[{ required: true, message: 'Please enter your username!' }]}
                  >
                    <Input
                      prefix={<UserOutlined />}
                      placeholder="Username"
                      style={{ borderRadius: '8px' }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="email"
                    rules={[
                      { required: true, message: 'Please enter your email!' },
                      { type: 'email', message: 'Please enter a valid email!' }
                    ]}
                  >
                    <Input
                      prefix={<MailOutlined />}
                      placeholder="Email"
                      style={{ borderRadius: '8px' }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="password"
                    rules={[{ required: true, message: 'Please enter your password!' }]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="Password"
                      style={{ borderRadius: '8px' }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="confirmPassword"
                    rules={[{ required: true, message: 'Please confirm your password!' }]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="Confirm Password"
                      style={{ borderRadius: '8px' }}
                    />
                  </Form.Item>

                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      style={{
                        width: '100%',
                        height: '48px',
                        borderRadius: '8px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        border: 'none',
                        fontSize: '16px',
                        fontWeight: 'bold'
                      }}
                    >
                      Create Account
                    </Button>
                  </Form.Item>
                </Form>
              </TabPane>
            </Tabs>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Login;




