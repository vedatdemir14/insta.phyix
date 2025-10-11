import React from 'react';
import { Layout, Menu, Typography, Button } from 'antd';
import { 
  ProjectOutlined, 
  UserOutlined,
  TeamOutlined,
  LogoutOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const { Sider } = Layout;
const { Title, Text } = Typography;

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const menuItems = [
    {
      key: '/campaigns',
      icon: <ProjectOutlined />,
      label: 'Campaigns',
    },
    {
      key: '/accounts',
      icon: <UserOutlined />,
      label: 'Accounts',
    },
    {
      key: '/leads',
      icon: <TeamOutlined />,
      label: 'Leads',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Sider
      width={250}
      style={{
        background: '#f5f5f5',
        boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
      }}
    >
      <div style={{ padding: '24px 16px', textAlign: 'center' }}>
        <div style={{ marginBottom: '16px' }}>
          <img 
            src="/logo.png" 
            alt="InstaPhyix Logo" 
            style={{ 
              width: '60px', 
              height: '60px',
              objectFit: 'contain'
            }} 
          />
        </div>
        <Title level={3} className="instagram-gradient" style={{ margin: 0, color: '#000000' }}>
          InstaPhyix
        </Title>
        {user && (
          <div style={{ marginTop: '8px' }}>
            <Text style={{ color: '#666666', fontSize: '14px' }}>
              Welcome, {user.full_name || user.username}
            </Text>
          </div>
        )}
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        style={{
          border: 'none',
          fontSize: '16px',
          background: '#f5f5f5',
          color: '#000000',
        }}
      />
      <div style={{ 
        position: 'absolute', 
        bottom: '24px', 
        left: '16px', 
        right: '16px' 
      }}>
        <Button
          type="text"
          icon={<LogoutOutlined />}
          onClick={handleLogout}
          style={{
            width: '100%',
            height: '40px',
            color: '#666666',
            border: '1px solid #d9d9d9',
            borderRadius: '8px'
          }}
        >
          Logout
        </Button>
      </div>
    </Sider>
  );
};

export default Sidebar;
