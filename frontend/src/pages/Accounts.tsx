import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  message, 
  Popconfirm,
  Space,
  Card
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import api from '../services/api';

const { Title, Text } = Typography;

interface InstagramAccount {
  id: string;
  username: string;
  password: string;
  is_active: boolean;
  created_at: string;
}

const Accounts: React.FC = () => {
  const [accounts, setAccounts] = useState<InstagramAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingAccount, setEditingAccount] = useState<InstagramAccount | null>(null);
  const [form] = Form.useForm();

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/instagram-accounts');
      const accountsData = response.data.data || [];
      setAccounts(accountsData);
    } catch (error) {
      console.error('Error fetching accounts:', error);
      message.error('Failed to fetch Instagram accounts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);


  const handleAdd = () => {
    setEditingAccount(null);
    // Keep form inputs filled - don't reset
    setModalVisible(true);
  };

  const handleEdit = (account: InstagramAccount) => {
    setEditingAccount(account);
    form.setFieldsValue({
      instagram_username: account.username,
      instagram_password: account.password,
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/instagram-accounts/${id}`);
      message.success('Instagram account deleted successfully');
      fetchAccounts();
    } catch (error) {
      console.error('Error deleting account:', error);
      message.error('Failed to delete Instagram account');
    }
  };

  const handleSubmit = async (values: { instagram_username: string; instagram_password: string }) => {
    try {
      if (editingAccount) {
        await api.put(`/instagram-accounts/${editingAccount.id}`, values);
        message.success('Instagram account updated successfully');
      } else {
        await api.post('/instagram-accounts', values);
        message.success('Instagram account added successfully');
      }
      setModalVisible(false);
      // Keep form inputs filled - don't reset
      fetchAccounts();
    } catch (error) {
      console.error('Error saving account:', error);
      message.error('Failed to save Instagram account');
    }
  };

  const columns = [
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: InstagramAccount) => (
        <Space>
          <Button
            type="primary"
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEdit(record)}
          >
            Edit
          </Button>
          <Popconfirm
            title="Are you sure you want to delete this account?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button
              type="primary"
              danger
              icon={<DeleteOutlined />}
              size="small"
            >
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ background: '#ffffff', minHeight: '100vh', padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ color: '#000000', margin: 0 }}>
          Instagram Accounts
        </Title>
        <Text style={{ color: '#666666' }}>
          Manage your Instagram accounts for scraping and campaigns
        </Text>
      </div>

      <Card>
        <div style={{ marginBottom: '16px' }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            Add Instagram Account
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={accounts}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
        />
      </Card>

      <Modal
        title={editingAccount ? 'Edit Instagram Account' : 'Add Instagram Account'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          // Keep form inputs filled - don't reset
        }}
        footer={null}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="instagram_username"
            label="Instagram Username"
            rules={[
              { required: true, message: 'Please enter Instagram username' },
              { min: 3, message: 'Username must be at least 3 characters' }
            ]}
          >
            <Input placeholder="Enter Instagram username" />
          </Form.Item>

          <Form.Item
            name="instagram_password"
            label="Instagram Password"
            rules={[
              { required: true, message: 'Please enter Instagram password' },
              { min: 6, message: 'Password must be at least 6 characters' }
            ]}
          >
            <Input.Password placeholder="Enter Instagram password" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                {editingAccount ? 'Update' : 'Add'} Account
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Accounts;
