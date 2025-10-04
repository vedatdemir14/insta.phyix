import React from 'react';
import { Layout, Menu, Typography } from 'antd';
import { 
  DashboardOutlined, 
  SearchOutlined, 
  MessageOutlined, 
  BarChartOutlined, 
  UserOutlined 
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Sider } = Layout;
const { Title } = Typography;

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/scraper',
      icon: <SearchOutlined />,
      label: 'Instagram Scraper',
    },
    {
      key: '/messages',
      icon: <MessageOutlined />,
      label: 'Messages',
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: 'Analytics',
    },
    {
      key: '/users',
      icon: <UserOutlined />,
      label: 'Users',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  return (
    <Sider
      width={250}
      style={{
        background: '#fff',
        boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
      }}
    >
      <div style={{ padding: '24px 16px', textAlign: 'center' }}>
        <Title level={3} className="instagram-gradient" style={{ margin: 0 }}>
          Instagram Scraper
        </Title>
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        style={{
          border: 'none',
          fontSize: '16px',
        }}
      />
    </Sider>
  );
};

export default Sidebar;
