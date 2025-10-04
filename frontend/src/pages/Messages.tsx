import React, { useState } from 'react';
import { Card, Form, Input, Button, InputNumber, message, Spin, Typography, List, Avatar } from 'antd';
import { MessageOutlined, SendOutlined, UserOutlined } from '@ant-design/icons';
import { apiService, MessageRequest } from '../services/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

const Messages: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [messageHistory, setMessageHistory] = useState<any[]>([]);

  const onFinish = async (values: MessageRequest) => {
    try {
      setLoading(true);
      
      message.loading('Sending message...', 0);
      
      const response = await apiService.sendMessage(values);
      
      message.destroy();
      message.success('Message sent successfully!');
      
      // Add to message history
      setMessageHistory(prev => [...prev, {
        id: Date.now(),
        username: values.username,
        message: values.message,
        timestamp: new Date().toLocaleString(),
        status: 'sent'
      }]);
      
      form.resetFields();
      
    } catch (error: any) {
      message.destroy();
      message.error(error.response?.data?.detail || 'Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={2}>Instagram Messages</Title>
      <Text type="secondary">Send messages to Instagram users</Text>
      
      <div style={{ marginTop: 24 }}>
        <Card title="Send Message" className="card-hover">
          <Form
            form={form}
            name="message"
            onFinish={onFinish}
            layout="vertical"
            initialValues={{
              delay_seconds: 2,
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
              label="Message"
              name="message"
              rules={[{ required: true, message: 'Please enter your message!' }]}
            >
              <TextArea
                rows={4}
                placeholder="Enter your message here..."
                maxLength={1000}
                showCount
              />
            </Form.Item>

            <Form.Item
              label="Delay (seconds)"
              name="delay_seconds"
              rules={[{ required: true, message: 'Please enter delay!' }]}
            >
              <InputNumber
                min={1}
                max={10}
                style={{ width: '100%' }}
                size="large"
                placeholder="Delay between actions"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                size="large"
                icon={<SendOutlined />}
                style={{ width: '100%' }}
              >
                Send Message
              </Button>
            </Form.Item>
          </Form>
        </Card>

        {messageHistory.length > 0 && (
          <Card title="Message History" style={{ marginTop: 24 }} className="card-hover">
            <List
              dataSource={messageHistory}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Avatar icon={<MessageOutlined />} />}
                    title={`@${item.username}`}
                    description={
                      <div>
                        <div>{item.message}</div>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {item.timestamp} • Status: {item.status}
                        </Text>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        )}
      </div>
    </div>
  );
};

export default Messages;
