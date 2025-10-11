import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Card, 
  Table, 
  Tag, 
  Button, 
  Space, 
  Row, 
  Col, 
  Statistic, 
  Select, 
  Input, 
  message,
  Modal,
  Descriptions,
  Avatar,
  Divider
} from 'antd';
import { 
  UserOutlined, 
  EyeOutlined, 
  EditOutlined, 
  DeleteOutlined,
  FilterOutlined,
  SearchOutlined,
  ExportOutlined,
  FlagOutlined,
  HeartOutlined,
  MessageOutlined
} from '@ant-design/icons';
import api from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface Lead {
  id: string;
  username: string;
  full_name: string;
  bio: string;
  followers_count: number;
  following_count: number;
  posts_count: number;
  is_verified: boolean;
  profile_pic_url: string;
  nationality: string;
  confidence: number;
  session_name: string;
  scraped_at: string;
}

interface Session {
  id: string;
  name?: string;
  session_name?: string;
  lead_count: number;
  created_at: string;
  last_updated: string;
}

const Leads: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [filteredLeads, setFilteredLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedSession, setSelectedSession] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [modalVisible, setModalVisible] = useState(false);

  // Fetch leads and sessions from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch leads
        console.log('🔍 Fetching leads from API...');
        const leadsResponse = await api.get('/leads');
        console.log('📊 Leads response:', leadsResponse.data);
        if (leadsResponse.data.success) {
          console.log('✅ Leads data received:', leadsResponse.data.data);
          console.log('📊 Leads count:', leadsResponse.data.data.length);
          setLeads(leadsResponse.data.data);
          setFilteredLeads(leadsResponse.data.data);
          console.log('🔄 State updated - leads:', leadsResponse.data.data);
        } else {
          console.log('❌ Leads response not successful:', leadsResponse.data);
        }
        
        // Fetch sessions
        console.log('🔍 Fetching sessions from API...');
        const sessionsResponse = await api.get('/leads/sessions');
        console.log('📊 Sessions response:', sessionsResponse.data);
        if (sessionsResponse.data.success) {
          console.log('✅ Sessions data received:', sessionsResponse.data.data);
          console.log('📋 First session structure:', sessionsResponse.data.data[0]);
          setSessions(sessionsResponse.data.data);
        } else {
          console.log('❌ Sessions response not successful:', sessionsResponse.data);
        }
      } catch (error) {
        console.error('Error fetching leads data:', error);
        message.error('Failed to load leads data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleSessionFilter = (sessionId: string) => {
    console.log('🔍 Session filter changed:', sessionId);
    console.log('📊 Available sessions:', sessions);
    setSelectedSession(sessionId);
    if (sessionId === 'all') {
      setFilteredLeads(leads);
    } else {
      const session = sessions.find(s => s.id === sessionId);
      console.log('🔍 Found session:', session);
      if (session) {
        const sessionName = session.name || session.session_name;
        console.log('🔍 Looking for session name:', sessionName);
        const filtered = leads.filter(lead => {
          console.log('🔍 Lead session name:', lead.session_name, 'vs', sessionName);
          return lead.session_name === sessionName;
        });
        console.log('📊 Filtered leads count:', filtered.length);
        setFilteredLeads(filtered);
      } else {
        console.log('❌ Session not found for ID:', sessionId);
        setFilteredLeads(leads);
      }
    }
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    const filtered = leads.filter(lead => 
      lead.username.toLowerCase().includes(value.toLowerCase()) ||
      lead.full_name.toLowerCase().includes(value.toLowerCase()) ||
      lead.bio.toLowerCase().includes(value.toLowerCase())
    );
    setFilteredLeads(filtered);
  };

  const handleViewLead = (lead: Lead) => {
    setSelectedLead(lead);
    setModalVisible(true);
  };

  const handleSendMessage = (lead: Lead) => {
    message.success(`Message sent to @${lead.username}`);
  };

  const handleExportLeads = () => {
    message.success('Leads exported successfully!');
  };

  const columns = [
    {
      title: 'Profile',
      key: 'profile',
      width: 200,
      render: (record: Lead) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Avatar 
            src={record.profile_pic_url} 
            icon={<UserOutlined />}
            size={40}
          />
          <div style={{ marginLeft: 12 }}>
            <div style={{ fontWeight: 'bold' }}>@{record.username}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {record.full_name}
            </div>
          </div>
        </div>
      ),
    },
    {
      title: 'Followers',
      dataIndex: 'followers_count',
      key: 'followers_count',
      width: 100,
      render: (count: number) => count.toLocaleString(),
    },
    {
      title: 'Posts',
      dataIndex: 'posts_count',
      key: 'posts_count',
      width: 80,
      render: (count: number) => count.toLocaleString(),
    },
    {
      title: 'Nationality',
      dataIndex: 'nationality',
      key: 'nationality',
      width: 120,
      render: (nationality: string, record: Lead) => (
        <Tag color={nationality.includes('TÜRK') ? 'green' : 'blue'}>
          {nationality}
        </Tag>
      ),
    },
    {
      title: 'Session',
      dataIndex: 'session_name',
      key: 'session_name',
      width: 150,
      render: (sessionName: string) => (
        <Tag color="purple">{sessionName}</Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (record: Lead) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />} 
            onClick={() => handleViewLead(record)}
          />
          <Button 
            type="link" 
            icon={<MessageOutlined />} 
            onClick={() => handleSendMessage(record)}
          />
        </Space>
      ),
    },
  ];

  const totalLeads = filteredLeads.length;
  const turkishLeads = filteredLeads.filter(lead => lead.nationality.includes('TÜRK')).length;
  const foreignLeads = filteredLeads.filter(lead => lead.nationality.includes('YABANCI')).length;
  const verifiedLeads = filteredLeads.filter(lead => lead.is_verified).length;

  // Debug state
  console.log('🔍 Current state:');
  console.log('📊 leads:', leads.length);
  console.log('📊 filteredLeads:', filteredLeads.length);
  console.log('📊 sessions:', sessions.length);
  console.log('📊 selectedSession:', selectedSession);

  return (
    <div style={{ 
      padding: '24px', 
      background: '#ffffff',
      minHeight: '100vh'
    }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ color: '#000000', margin: 0 }}>
          Leads Management
        </Title>
        <Text style={{ color: '#666666' }}>
          Manage and analyze your scraped leads by sessions
        </Text>
      </div>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Leads"
              value={totalLeads}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Turkish Leads"
              value={turkishLeads}
              prefix={<FlagOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Foreign Leads"
              value={foreignLeads}
              prefix={<FlagOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Verified Accounts"
              value={verifiedLeads}
              prefix={<HeartOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8}>
            <Text strong>Filter by Session:</Text>
            <Select
              value={selectedSession}
              onChange={handleSessionFilter}
              style={{ width: '100%', marginTop: 8 }}
              placeholder="Select session"
            >
              <Option value="all">All Sessions ({leads.length})</Option>
              {sessions.map((session, index) => {
                console.log(`📋 Session ${index}:`, session);
                return (
                  <Option key={session.id || index} value={session.id || index}>
                    {session.name || session.session_name || `Session ${index}`} ({session.lead_count || 0})
                  </Option>
                );
              })}
            </Select>
          </Col>
          <Col xs={24} sm={8}>
            <Text strong>Search Leads:</Text>
            <Input
              placeholder="Search by username, name, or bio"
              prefix={<SearchOutlined />}
              onChange={(e) => handleSearch(e.target.value)}
              style={{ marginTop: 8 }}
            />
          </Col>
          <Col xs={24} sm={8}>
            <Space style={{ marginTop: 24 }}>
              <Button 
                type="primary" 
                icon={<ExportOutlined />}
                onClick={handleExportLeads}
              >
                Export Leads
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Leads Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredLeads}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} leads`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Lead Detail Modal */}
      <Modal
        title={`Lead Details - @${selectedLead?.username}`}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)}>
            Close
          </Button>,
          <Button 
            key="message" 
            type="primary" 
            icon={<MessageOutlined />}
            onClick={() => {
              handleSendMessage(selectedLead!);
              setModalVisible(false);
            }}
          >
            Send Message
          </Button>
        ]}
        width={600}
      >
        {selectedLead && (
          <div>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <Avatar 
                src={selectedLead.profile_pic_url} 
                size={80}
                icon={<UserOutlined />}
              />
              <div style={{ marginTop: 16 }}>
                <Title level={3}>@{selectedLead.username}</Title>
                <Text type="secondary">{selectedLead.full_name}</Text>
              </div>
            </div>

            <Descriptions column={1} bordered>
              <Descriptions.Item label="Bio">
                {selectedLead.bio || 'No bio available'}
              </Descriptions.Item>
              <Descriptions.Item label="Followers">
                {selectedLead.followers_count.toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="Following">
                {selectedLead.following_count.toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="Posts">
                {selectedLead.posts_count.toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="Verified">
                <Tag color={selectedLead.is_verified ? 'green' : 'red'}>
                  {selectedLead.is_verified ? 'Yes' : 'No'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Nationality">
                <Tag color={selectedLead.nationality.includes('TÜRK') ? 'green' : 'blue'}>
                  {selectedLead.nationality}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Confidence">
                <Tag color={selectedLead.confidence >= 90 ? 'green' : 'orange'}>
                  {selectedLead.confidence}%
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Session">
                <Tag color="purple">{selectedLead.session_name}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Scraped At">
                {new Date(selectedLead.scraped_at).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Leads;
