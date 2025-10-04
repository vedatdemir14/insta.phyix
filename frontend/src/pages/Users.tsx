import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Popconfirm, message, Typography, Tag, Avatar, Space } from 'antd';
import { DeleteOutlined, UserOutlined, EyeOutlined } from '@ant-design/icons';
import { apiService, UserData } from '../services/api';

const { Title, Text } = Typography;

const Users: React.FC = () => {
  const [users, setUsers] = useState<UserData[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await apiService.getUsers();
      setUsers(response.data);
    } catch (error: any) {
      message.error('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (username: string) => {
    try {
      await apiService.deleteUser(username);
      message.success(`User ${username} deleted successfully`);
      fetchUsers(); // Refresh the list
    } catch (error: any) {
      message.error('Failed to delete user');
    }
  };

  const columns = [
    {
      title: 'User',
      dataIndex: 'username',
      key: 'username',
      render: (username: string, record: UserData) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div style={{ fontWeight: 'bold' }}>@{username}</div>
            {record.full_name && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {record.full_name}
              </Text>
            )}
          </div>
        </Space>
      ),
    },
    {
      title: 'Followers',
      dataIndex: 'followers_count',
      key: 'followers_count',
      render: (count: number) => count ? count.toLocaleString() : 'N/A',
    },
    {
      title: 'Following',
      dataIndex: 'following_count',
      key: 'following_count',
      render: (count: number) => count ? count.toLocaleString() : 'N/A',
    },
    {
      title: 'Posts',
      dataIndex: 'posts_count',
      key: 'posts_count',
      render: (count: number) => count ? count.toLocaleString() : 'N/A',
    },
    {
      title: 'Bio',
      dataIndex: 'bio',
      key: 'bio',
      render: (bio: string) => bio ? (
        <Text ellipsis={{ tooltip: bio }} style={{ maxWidth: 200 }}>
          {bio}
        </Text>
      ) : 'N/A',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: UserData) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => message.info(`Viewing ${record.username} details`)}
          >
            View
          </Button>
          <Popconfirm
            title="Are you sure you want to delete this user?"
            onConfirm={() => handleDeleteUser(record.username)}
            okText="Yes"
            cancelText="No"
          >
            <Button
              type="primary"
              danger
              size="small"
              icon={<DeleteOutlined />}
            >
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Users</Title>
      <Text type="secondary">Manage scraped Instagram users</Text>
      
      <Card style={{ marginTop: 24 }} className="card-hover">
        <Table
          columns={columns}
          dataSource={users}
          loading={loading}
          rowKey="username"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} users`,
          }}
          scroll={{ x: 800 }}
        />
      </Card>
    </div>
  );
};

export default Users;
