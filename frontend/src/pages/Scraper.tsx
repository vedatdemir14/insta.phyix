import React, { useState } from 'react';
import { Card, Form, Input, Button, InputNumber, Switch, message, Spin, Row, Col, Typography, Divider } from 'antd';
import { SearchOutlined, UserOutlined, PictureOutlined } from '@ant-design/icons';
import { apiService, ScrapeRequest } from '../services/api';

const { Title, Text } = Typography;

const Scraper: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [scrapeResult, setScrapeResult] = useState<any>(null);

  const onFinish = async (values: ScrapeRequest) => {
    try {
      setLoading(true);
      setScrapeResult(null);
      
      message.loading('Scraping Instagram profile...', 0);
      
      const response = await apiService.scrapeProfile(values);
      
      message.destroy();
      message.success('Profile scraped successfully!');
      setScrapeResult(response.data);
      
    } catch (error: any) {
      message.destroy();
      message.error(error.response?.data?.detail || 'Failed to scrape profile');
    } finally {
      setLoading(false);
    }
  };

  const onFinishFailed = (errorInfo: any) => {
    console.log('Failed:', errorInfo);
    message.error('Please fill in all required fields');
  };

  return (
    <div>
      <Title level={2}>Instagram Scraper</Title>
      <Text type="secondary">Scrape Instagram profiles and posts data</Text>
      
      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Scrape Configuration" className="card-hover">
            <Form
              form={form}
              name="scraper"
              onFinish={onFinish}
              onFinishFailed={onFinishFailed}
              layout="vertical"
              initialValues={{
                max_posts: 10,
                include_stories: false,
              }}
            >
              <Form.Item
                label="Instagram Username"
                name="username"
                rules={[{ required: true, message: 'Please enter Instagram username!' }]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="Enter Instagram username (without @)"
                  size="large"
                />
              </Form.Item>

              <Form.Item
                label="Maximum Posts to Scrape"
                name="max_posts"
                rules={[{ required: true, message: 'Please enter maximum posts!' }]}
              >
                <InputNumber
                  min={1}
                  max={100}
                  style={{ width: '100%' }}
                  size="large"
                  placeholder="Number of posts to scrape"
                />
              </Form.Item>

              <Form.Item
                label="Include Stories"
                name="include_stories"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                label="Session Name"
                name="session_name"
                rules={[{ required: true, message: 'Please enter session name!' }]}
              >
                <Input
                  placeholder="Enter session name (e.g., Location Scraping - Istanbul)"
                  size="large"
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  size="large"
                  icon={<SearchOutlined />}
                  style={{ width: '100%' }}
                >
                  Start Scraping
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="Scrape Results" className="card-hover">
            {loading ? (
              <div className="loading-container">
                <Spin size="large" />
                <div style={{ marginTop: 16 }}>
                  <Text>Scraping in progress...</Text>
                </div>
              </div>
            ) : scrapeResult ? (
              <div>
                <Row gutter={[16, 16]}>
                  <Col span={24}>
                    <div style={{ textAlign: 'center', marginBottom: 16 }}>
                      <UserOutlined style={{ fontSize: 48, color: '#667eea' }} />
                      <Title level={3} style={{ margin: '8px 0' }}>
                        @{scrapeResult.username}
                      </Title>
                      <Text type="secondary">{scrapeResult.full_name}</Text>
                    </div>
                  </Col>
                </Row>

                <Divider />

                <Row gutter={[16, 16]}>
                  <Col span={8}>
                    <div style={{ textAlign: 'center' }}>
                      <Title level={4} style={{ margin: 0, color: '#667eea' }}>
                        {scrapeResult.followers_count?.toLocaleString() || 'N/A'}
                      </Title>
                      <Text type="secondary">Followers</Text>
                    </div>
                  </Col>
                  <Col span={8}>
                    <div style={{ textAlign: 'center' }}>
                      <Title level={4} style={{ margin: 0, color: '#52c41a' }}>
                        {scrapeResult.following_count?.toLocaleString() || 'N/A'}
                      </Title>
                      <Text type="secondary">Following</Text>
                    </div>
                  </Col>
                  <Col span={8}>
                    <div style={{ textAlign: 'center' }}>
                      <Title level={4} style={{ margin: 0, color: '#fa8c16' }}>
                        {scrapeResult.posts_count?.toLocaleString() || 'N/A'}
                      </Title>
                      <Text type="secondary">Posts</Text>
                    </div>
                  </Col>
                </Row>

                {scrapeResult.bio && (
                  <>
                    <Divider />
                    <div>
                      <Text strong>Bio:</Text>
                      <div style={{ marginTop: 8 }}>
                        <Text>{scrapeResult.bio}</Text>
                      </div>
                    </div>
                  </>
                )}

                {scrapeResult.posts && scrapeResult.posts.length > 0 && (
                  <>
                    <Divider />
                    <div>
                      <Text strong>Recent Posts ({scrapeResult.posts.length}):</Text>
                      <div style={{ marginTop: 8, maxHeight: 200, overflowY: 'auto' }}>
                        {scrapeResult.posts.map((post: any, index: number) => (
                          <div key={index} style={{ marginBottom: 8, padding: 8, background: '#f5f5f5', borderRadius: 4 }}>
                            <Text>{post.caption?.substring(0, 100)}...</Text>
                            <br />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              ❤️ {post.likes_count} • 💬 {post.comments_count}
                            </Text>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <SearchOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">No scrape results yet</Text>
                  <br />
                  <Text type="secondary">Enter a username and click "Start Scraping"</Text>
                </div>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Scraper;






