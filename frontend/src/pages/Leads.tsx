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
  Divider,
  Form
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
import api, { apiService } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface Lead {
  id: string;
  username: string;
  full_name: string;
  bio: string;
  biography: string;  // Add biography field
  followers_count: number;
  following_count: number;
  posts_count: number;
  is_verified: boolean;
  profile_pic_url: string;
  nationality: string;
  confidence: number;
  session_name: string;
  scraped_at: string;
  created_at?: string;  // Add created_at field
  last_updated?: string;  // Add last_updated field
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
  const [editNationalityModal, setEditNationalityModal] = useState(false);
  const [editingLead, setEditingLead] = useState<Lead | null>(null);
  const [newNationality, setNewNationality] = useState('');
  const [form] = Form.useForm();
  const [tableKey, setTableKey] = useState(0); // Force re-render key

  // Debug modal state
  useEffect(() => {
    if (editNationalityModal && editingLead) {
      console.log('🔍 Modal opened for:', editingLead.username);
    }
  }, [editNationalityModal, editingLead]);

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
          
          // Sort leads by creation date (newest first)
          const sortedLeads = leadsResponse.data.data.sort((a: Lead, b: Lead) => {
            const dateA = new Date(a.created_at || a.scraped_at || 0);
            const dateB = new Date(b.created_at || b.scraped_at || 0);
            return dateB.getTime() - dateA.getTime(); // Newest first
          });
          
          setLeads(sortedLeads);
          setFilteredLeads(sortedLeads);
          console.log('🔄 State updated - leads:', sortedLeads);
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
      // Sort all leads by creation date (newest first)
      const sortedLeads = [...leads].sort((a, b) => {
        const dateA = new Date(a.created_at || a.scraped_at || 0);
        const dateB = new Date(b.created_at || b.scraped_at || 0);
        return dateB.getTime() - dateA.getTime(); // Newest first
      });
      setFilteredLeads(sortedLeads);
    } else {
      // Find session by index or name
      const sessionIndex = parseInt(sessionId);
      const session = sessions[sessionIndex];
      console.log('🔍 Found session:', session);
      if (session) {
        const sessionName = session.name || session.session_name;
        console.log('🔍 Looking for session name:', sessionName);
        let filtered = leads.filter(lead => {
          console.log('🔍 Lead session name:', lead.session_name, 'vs', sessionName);
          return lead.session_name === sessionName;
        });
        
        // Sort filtered leads by creation date (newest first)
        filtered.sort((a, b) => {
          const dateA = new Date(a.created_at || a.scraped_at || 0);
          const dateB = new Date(b.created_at || b.scraped_at || 0);
          return dateB.getTime() - dateA.getTime(); // Newest first
        });
        
        console.log('📊 Filtered leads count:', filtered.length);
        setFilteredLeads(filtered);
      } else {
        console.log('❌ Session not found for index:', sessionId);
        setFilteredLeads(leads);
      }
    }
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    let filtered = leads.filter(lead => 
      lead.username.toLowerCase().includes(value.toLowerCase()) ||
      lead.full_name.toLowerCase().includes(value.toLowerCase()) ||
      (lead.bio && lead.bio.toLowerCase().includes(value.toLowerCase())) ||
      (lead.biography && lead.biography.toLowerCase().includes(value.toLowerCase()))
    );
    
    // Sort by creation date (newest first)
    filtered.sort((a, b) => {
      const dateA = new Date(a.created_at || a.scraped_at || 0);
      const dateB = new Date(b.created_at || b.scraped_at || 0);
      return dateB.getTime() - dateA.getTime(); // Newest first
    });
    
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

  const handleMergeData = async () => {
    try {
      setLoading(true);
      const response = await api.post('/leads/merge-data');
      
      if (response.data.success) {
        message.success(`Data merge completed! ${response.data.leads_count} leads, ${response.data.sessions_count} sessions`);
        
        // Refresh the data
        const leadsResponse = await api.get('/leads');
        if (leadsResponse.data.success) {
          setLeads(leadsResponse.data.data);
          setFilteredLeads(leadsResponse.data.data);
        }
        
        const sessionsResponse = await api.get('/leads/sessions');
        if (sessionsResponse.data.success) {
          setSessions(sessionsResponse.data.data);
        }
      } else {
        message.error('Failed to merge data');
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to merge data');
    } finally {
      setLoading(false);
    }
  };

  const handleEditNationality = (lead: Lead) => {
    console.log('🔍 Edit nationality clicked for:', lead.username);
    setEditingLead(lead);
    setNewNationality(lead.nationality);
    setEditNationalityModal(true);
    console.log('🔍 Modal should be open now');
  };

  const handleSaveNationality = async () => {
    console.log('🔍 Save nationality clicked');
    console.log('📊 editingLead:', editingLead);
    console.log('📊 newNationality:', newNationality);
    
    if (!editingLead || !newNationality.trim()) {
      message.error('Please enter a nationality');
      return;
    }

    try {
      setLoading(true);
      console.log('🔄 Calling updateNationality API...');
      const result = await apiService.updateNationality(editingLead.username, newNationality);
      console.log('✅ API response:', result);
      
      // Update the lead in local state
      const updatedLeads = leads.map(lead => 
        lead.username === editingLead.username 
          ? { ...lead, nationality: newNationality, last_updated: new Date().toISOString() }
          : lead
      );
      setLeads(updatedLeads);
      
      // Also update filteredLeads
      const updatedFilteredLeads = filteredLeads.map(lead => 
        lead.username === editingLead.username 
          ? { ...lead, nationality: newNationality, last_updated: new Date().toISOString() }
          : lead
      );
      setFilteredLeads(updatedFilteredLeads);
      
      console.log('✅ Updated leads:', updatedLeads.length);
      console.log('✅ Updated filtered leads:', updatedFilteredLeads.length);
      
      message.success(`Nationality updated to ${newNationality} for @${editingLead.username}`);
      setEditNationalityModal(false);
      setEditingLead(null);
      setNewNationality('');
      
      // Force table re-render
      setTableKey(prev => prev + 1);
    } catch (error: any) {
      console.error('❌ Error updating nationality:', error);
      message.error(error.response?.data?.detail || 'Failed to update nationality');
    } finally {
      setLoading(false);
    }
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
      width: 150,
      render: (nationality: string, record: Lead) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Tag color={nationality.includes('TÜRK') ? 'green' : 'blue'}>
            {nationality}
          </Tag>
          <Button 
            type="link" 
            size="small"
            icon={<EditOutlined />} 
            onClick={() => {
              console.log('🔍 EDIT BUTTON CLICKED!');
              console.log('📊 Record:', record);
              handleEditNationality(record);
            }}
            style={{ padding: '0 4px' }}
          />
        </div>
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
                  <Option key={index} value={index.toString()}>
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
              <Button 
                type="default" 
                icon={<FlagOutlined />}
                onClick={handleMergeData}
                loading={loading}
              >
                Merge Data
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Leads Table */}
      <Card>
        <Table
          key={tableKey}
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
                {selectedLead.bio || selectedLead.biography || 'No bio available'}
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

      {/* Edit Nationality Modal */}
      <Modal
        title={`Edit Nationality - @${editingLead?.username}`}
        open={editNationalityModal}
        onCancel={() => {
          console.log('🔍 Modal cancelled');
          setEditNationalityModal(false);
          setEditingLead(null);
          setNewNationality('');
        }}
        footer={[
          <Button key="cancel" onClick={() => {
            setEditNationalityModal(false);
            setEditingLead(null);
            setNewNationality('');
          }}>
            Cancel
          </Button>,
          <Button 
            key="save" 
            type="primary" 
            loading={loading}
            onClick={() => {
              console.log('🔍 Save button clicked!');
              handleSaveNationality();
            }}
          >
            Save
          </Button>
        ]}
        width={500}
      >
        {editingLead && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>Current Nationality:</Text>
              <div style={{ marginTop: 8 }}>
                <Tag color={editingLead.nationality.includes('TÜRK') ? 'green' : 'blue'}>
                  {editingLead.nationality}
                </Tag>
              </div>
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <Text strong>Bio:</Text>
              <div style={{ marginTop: 8, padding: 8, background: '#f5f5f5', borderRadius: 4 }}>
                <Text>{editingLead.bio || editingLead.biography || 'No bio available'}</Text>
              </div>
            </div>

            <Form.Item label="New Nationality:">
              <Input
                value={newNationality}
                onChange={(e) => setNewNationality(e.target.value)}
                placeholder="Enter new nationality"
                size="large"
              />
            </Form.Item>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Leads;
