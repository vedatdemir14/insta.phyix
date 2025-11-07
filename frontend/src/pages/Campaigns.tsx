import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Tabs, 
  Card, 
  Form, 
  Input, 
  Button, 
  Select, 
  InputNumber, 
  Upload, 
  message,
  Space,
  Row,
  Col,
  Divider,
  Tag,
  Table,
  Radio,
  Checkbox,
  Modal
} from 'antd';
import { 
  EnvironmentOutlined, 
  UploadOutlined, 
  UserOutlined, 
  FlagOutlined, 
  MessageOutlined, 
  SendOutlined 
} from '@ant-design/icons';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface InstagramAccount {
  id: string;
  username: string;
  password: string;
  is_active: boolean;
}

const Campaigns: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [instagramAccounts, setInstagramAccounts] = useState<InstagramAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [locationScrapingResults, setLocationScrapingResults] = useState<string[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [profileScrapingResults, setProfileScrapingResults] = useState<any[]>([]);
  const [showProfileResults, setShowProfileResults] = useState(false);
  const [nationalityResults, setNationalityResults] = useState<any[]>([]);
  const [showNationalityResults, setShowNationalityResults] = useState(false);

  // Fetch user-specific data on component mount
  useEffect(() => {
    if (!isAuthenticated) {
      message.warning('Please login to access campaigns');
      return;
    }

    const fetchUserData = async () => {
      try {
        const [accountsResponse, leadsResponse, sessionsResponse, templatesResponse] = await Promise.all([
          api.get('/instagram-accounts'),
          api.get('/leads'),
          api.get('/leads/sessions'),
          api.get('/message-templates')
        ]);
        
        if (accountsResponse.data.success) {
          setInstagramAccounts(accountsResponse.data.data);
          console.log('🔍 Fetched user Instagram accounts:', accountsResponse.data.data);
        }
        
        if (leadsResponse.data.success) {
          console.log('🔍 Fetched user leads:', leadsResponse.data.data);
        }
        
        if (sessionsResponse.data.success) {
          console.log('🔍 Fetched user sessions:', sessionsResponse.data.data);
        }
        
        if (templatesResponse.data.success) {
          console.log('🔍 Fetched user templates:', templatesResponse.data.data);
        }
        
      } catch (error) {
        console.error('Error fetching user data:', error);
        message.error('Failed to fetch user data');
      }
    };

    fetchUserData();
  }, [isAuthenticated]);


  const fetchInstagramAccounts = async () => {
    try {
      const response = await api.get('/instagram-accounts');
      setInstagramAccounts(response.data.accounts || []);
    } catch (error) {
      console.error('Error fetching Instagram accounts:', error);
    }
  };

  const LocationScrapingTab: React.FC = () => {
    const [form] = Form.useForm();

    const onFinish = async (values: any) => {
      try {
        setLoading(true);
        
        // Find selected Instagram account
        const selectedAccount = instagramAccounts.find(acc => acc.id === values.instagram_account_id);
        if (!selectedAccount) {
          message.error('Please select a valid Instagram account');
          return;
        }
        
        // Parse location URLs
        const locationUrls = values.location_urls
          ? values.location_urls.split('\n').filter(url => url.trim())
          : [];
        
        // Prepare request data according to backend model
        const requestData = {
          session_name: values.session_name,
          ig_user: selectedAccount.username,
          ig_pass: selectedAccount.password,
          locations: locationUrls,
          max_profiles: values.max_profiles || 50
        };
        
        const response = await api.post('/campaigns/location-scraping', requestData);
        
        // Debug: Log the response
        console.log('Location scraping response:', response.data);
        
        // Handle results
        if (response.data && response.data.data && response.data.data.usernames) {
          const usernames = response.data.data.usernames;
          setLocationScrapingResults(usernames);
          setShowResults(true);
          message.success(`Location scraping completed! Found ${usernames.length} usernames.`);
          
          // Auto-fill profile scraping form
          const profileForm = document.querySelector('[data-profile-form]') as any;
          if (profileForm) {
            const profileTextArea = profileForm.querySelector('textarea[name="usernames"]');
            if (profileTextArea) {
              profileTextArea.value = usernames.join('\n');
            }
          }
        } else {
          message.success('Location scraping campaign started successfully!');
        }
        
        // Keep form inputs filled - don't reset
      } catch (error) {
        console.error('Error starting location scraping:', error);
        message.error('Failed to start location scraping campaign');
      } finally {
        setLoading(false);
      }
    };

    return (
      <Card>
        <Title level={3}>
          <EnvironmentOutlined /> Location Scraping
        </Title>
        <Text type="secondary">
          Fetch usernames from Instagram locations
        </Text>
        
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          style={{ marginTop: 24 }}
        >
          <Form.Item
            name="session_name"
            label="Session Name"
            rules={[{ required: true, message: 'Please enter session name' }]}
          >
            <Input placeholder="e.g., Istanbul Cafes, Ankara Shopping, etc." />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="instagram_account_id"
                label="Instagram Account"
                rules={[{ required: true, message: 'Please select Instagram account' }]}
              >
                <Select placeholder="Select Instagram account">
                  {instagramAccounts.map(account => (
                    <Option key={account.id} value={account.id}>
                      {account.username}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="max_profiles"
                label="Max Profiles per Location"
                rules={[{ required: true, message: 'Please enter max profiles' }]}
              >
                <InputNumber
                  min={1}
                  max={100}
                  defaultValue={50}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="location_urls"
            label="Location URLs or IDs"
            rules={[{ required: true, message: 'Please enter location URLs' }]}
          >
            <TextArea
              rows={4}
              placeholder="https://www.instagram.com/explore/locations/123456789/&#10;https://www.instagram.com/explore/locations/987654321/"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<EnvironmentOutlined />}
              size="large"
            >
              Start Location Scraping
            </Button>
          </Form.Item>
        </Form>

        {/* Results Section */}
        {showResults && locationScrapingResults.length > 0 && (
          <Card style={{ marginTop: 24, backgroundColor: '#f6ffed', border: '1px solid #b7eb8f' }}>
            <Title level={4} style={{ color: '#52c41a' }}>
              ✅ Location Scraping Results
            </Title>
            <Text>
              Found <strong>{locationScrapingResults.length}</strong> usernames from location scraping.
              These usernames have been automatically loaded into the Profile Scraping section below.
            </Text>
            
            <div style={{ marginTop: 16, maxHeight: 200, overflowY: 'auto' }}>
              <Text strong>Scraped Usernames:</Text>
              <div style={{ marginTop: 8 }}>
                {locationScrapingResults.slice(0, 20).map((username, index) => (
                  <Tag key={index} color="green" style={{ margin: '2px' }}>
                    {username}
                  </Tag>
                ))}
                {locationScrapingResults.length > 20 && (
                  <Tag color="blue">+{locationScrapingResults.length - 20} more...</Tag>
                )}
              </div>
            </div>
          </Card>
        )}
      </Card>
    );
  };

  const UploadProfilesTab: React.FC = () => {
    const [form] = Form.useForm();

    const onFinish = async (values: any) => {
      try {
        setLoading(true);
        const response = await api.post('/campaigns/profile-scraping', values);
        message.success('Profile scraping campaign started successfully!');
        // Keep form inputs filled - don't reset
      } catch (error) {
        console.error('Error starting profile scraping:', error);
        message.error('Failed to start profile scraping campaign');
      } finally {
        setLoading(false);
      }
    };

    return (
      <Card>
        <Title level={3}>
          <UploadOutlined /> Upload Profiles
        </Title>
        <Text type="secondary">
          Upload profile usernames for scraping
        </Text>
        
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          style={{ marginTop: 24 }}
        >
          <Form.Item
            name="session_name"
            label="Session Name"
            rules={[{ required: true, message: 'Please enter session name' }]}
          >
            <Input placeholder="e.g., Target Profiles, Customer List, etc." />
          </Form.Item>

          <Form.Item
            name="usernames"
            label="Profile Usernames"
            rules={[{ required: true, message: 'Please enter usernames' }]}
          >
            <TextArea
              rows={6}
              placeholder="username1&#10;username2&#10;username3"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<UploadOutlined />}
              size="large"
            >
              Start Profile Scraping
            </Button>
          </Form.Item>
        </Form>
      </Card>
    );
  };

  const ProfileScrapingTab: React.FC = () => {
    const [form] = Form.useForm();

    // Auto-fill usernames when location scraping results are available
    useEffect(() => {
      if (locationScrapingResults.length > 0) {
        form.setFieldsValue({
          usernames: locationScrapingResults.join('\n')
        });
      }
    }, [locationScrapingResults, form]);

    const onFinish = async (values: any) => {
      try {
        setLoading(true);
        
        // Parse usernames from textarea (split by newlines)
        const rawUsernames = values.usernames 
          ? values.usernames.split('\n').filter((u: string) => u.trim())
          : [];
        
        // Convert Instagram URLs to usernames
        const usernames = rawUsernames.map((item: string) => {
          if (item.includes('instagram.com/')) {
            // Extract username from Instagram URL
            const match = item.match(/instagram\.com\/([^\/\?]+)/);
            return match ? match[1] : item;
          }
          return item;
        });
        
        // Prepare request data according to backend model
        const requestData = {
          usernames: usernames,
          max_profiles: values.max_profiles || 100
        };
        
        console.log('Profile scraping request:', requestData);
        
        const response = await api.post('/campaigns/profile-scraping', requestData);
        console.log('Profile scraping response:', response.data);
        
        // Handle results
        if (response.data && response.data.data && response.data.data.profiles) {
          const profiles = response.data.data.profiles;
          setProfileScrapingResults(profiles);
          setShowProfileResults(true);
          message.success(`Profile scraping completed! Found ${profiles.length} profiles.`);
        } else {
          message.success('Profile scraping campaign started successfully!');
        }
        
        // Keep form inputs filled - don't reset
      } catch (error) {
        console.error('Error starting profile scraping:', error);
        message.error('Failed to start profile scraping campaign');
      } finally {
        setLoading(false);
      }
    };

    return (
      <Card>
        <Title level={3}>
          <UserOutlined /> Profile Scraping
        </Title>
        <Text type="secondary">
          Scrape detailed profile information
        </Text>
        
        {/* Warning Message */}
        <div style={{ 
          marginTop: 16, 
          padding: 12, 
          backgroundColor: '#fff2e8', 
          border: '1px solid #ffb366', 
          borderRadius: 6 
        }}>
          <Text style={{ color: '#d46b08', fontWeight: 'bold' }}>
            ⚠️ Warning: To scrape profiles from a location, please do location scraping first.
          </Text>
        </div>
        
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          style={{ marginTop: 24 }}
          data-profile-form="true"
        >
          <Form.Item
            name="session_name"
            label="Session Name"
            rules={[{ required: true, message: 'Please enter session name' }]}
          >
            <Input placeholder="e.g., Profile Analysis, User Research, etc." />
          </Form.Item>

          <Form.Item
            name="usernames"
            label="Profile Usernames"
            rules={[{ required: true, message: 'Please enter usernames' }]}
          >
            <TextArea
              rows={6}
              placeholder="username1&#10;username2&#10;username3"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<UserOutlined />}
              size="large"
            >
              Start Profile Scraping
            </Button>
          </Form.Item>
        </Form>
        
        {/* Results Section */}
        {showProfileResults && profileScrapingResults.length > 0 && (
          <Card style={{ marginTop: 24, backgroundColor: '#f0f9ff', border: '1px solid #91d5ff' }}>
            <Title level={4} style={{ color: '#1890ff' }}>
              ✅ Profile Scraping Results
            </Title>
            <Text>
              Found <strong>{profileScrapingResults.length}</strong> profiles with detailed information.
            </Text>
            
            <div style={{ marginTop: 16, maxHeight: 300, overflowY: 'auto' }}>
              <Text strong>Scraped Profiles:</Text>
              <div style={{ marginTop: 8 }}>
                {profileScrapingResults.slice(0, 10).map((profile, index) => (
                  <Card key={index} size="small" style={{ margin: '4px 0', backgroundColor: '#fafafa' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <Text strong>@{profile.username}</Text>
                        <br />
                        <Text type="secondary">{profile.full_name}</Text>
                        <br />
                        <Text type="secondary">{profile.bio}</Text>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div>👥 {profile.followers_count?.toLocaleString()}</div>
                        <div>📸 {profile.posts_count}</div>
                        {profile.is_verified && <Tag color="blue">Verified</Tag>}
                        {profile.is_private && <Tag color="orange">Private</Tag>}
                      </div>
                    </div>
                  </Card>
                ))}
                {profileScrapingResults.length > 10 && (
                  <Tag color="blue">+{profileScrapingResults.length - 10} more profiles...</Tag>
                )}
              </div>
            </div>
          </Card>
        )}
      </Card>
    );
  };

  const NationalityClassificationTab: React.FC = () => {
    const [form] = Form.useForm();
    const [editingNationality, setEditingNationality] = React.useState<any>(null);
    const [editModalVisible, setEditModalVisible] = React.useState(false);

    // Nationality editing functions
    const handleNationalityEdit = (record: any) => {
      console.log('🔍 EDIT BUTTON CLICKED IN CAMPAIGNS!');
      console.log('📊 Record:', record);
      setEditingNationality(record);
      setEditModalVisible(true);
      console.log('🔍 Modal should be open now');
    };

    const handleNationalitySwap = async (record: any) => {
      try {
        const newNationality = record.nationality?.includes('TÜRK') ? 'YABANCI' : 'TÜRK';
        await updateNationalityInSupabase(record.username, newNationality);
        
        // Update local state
        const updatedResults = nationalityResults.map(item => 
          item.username === record.username 
            ? { ...item, nationality: newNationality }
            : item
        );
        setNationalityResults(updatedResults);
        
        message.success(`Nationality updated to ${newNationality} for @${record.username}`);
      } catch (error) {
        console.error('Error updating nationality:', error);
        message.error('Failed to update nationality');
      }
    };

    const updateNationalityInSupabase = async (username: string, newNationality: string) => {
      try {
        const response = await api.post('/leads/update-nationality', {
          username: username,
          nationality: newNationality
        });
        return response.data;
      } catch (error) {
        console.error('Error updating nationality in Supabase:', error);
        throw error;
      }
    };

    const handleEditSave = async (values: any) => {
      console.log('🔍 HANDLE EDIT SAVE CALLED!');
      console.log('📊 Values:', values);
      console.log('📊 Editing nationality:', editingNationality);
      
      try {
        console.log('🔄 Updating nationality in Supabase...');
        await updateNationalityInSupabase(editingNationality.username, values.nationality);
        
        // Update local state
        const updatedResults = nationalityResults.map(item => 
          item.username === editingNationality.username 
            ? { ...item, nationality: values.nationality }
            : item
        );
        setNationalityResults(updatedResults);
        
        console.log('✅ Nationality updated successfully');
        message.success(`Nationality updated to ${values.nationality} for @${editingNationality.username}`);
        setEditModalVisible(false);
        setEditingNationality(null);
      } catch (error) {
        console.error('❌ Error updating nationality:', error);
        message.error('Failed to update nationality');
      }
    };

    const onFinish = async (values: any) => {
      try {
        setLoading(true);
        
        // Extract usernames from profile scraping results
        const usernames = profileScrapingResults.map(profile => profile.username);
        
        // Prepare request data according to backend model
        const requestData = {
          usernames: usernames,
          session_name: values.session_name || `Nationality Classification - ${new Date().toLocaleString()}`
        };
        
        console.log('Nationality classification request:', requestData);
        
        const response = await api.post('/campaigns/nationality-classification', requestData);
        console.log('Nationality classification response:', response.data);
        
        // Handle results
        if (response.data && response.data.data && response.data.data.classifications) {
          const classifications = response.data.data.classifications;
          console.log('🔍 Frontend: Raw classifications:', classifications);
          console.log('🔍 Frontend: First item:', classifications[0]);
          
          // Map the response data to match frontend expectations
          const mappedResults = classifications.map((item: any) => {
            console.log('🔍 Frontend: Mapping item:', item);
            console.log('🔍 Frontend: item.Nationality:', item.Nationality);
            console.log('🔍 Frontend: item keys:', Object.keys(item));
            
            return {
              username: item.username,
              full_name: item.full_name,
              bio: item.bio || '',
              nationality: item.Nationality || 'UNKNOWN',
              confidence: 95
            };
          });
          setNationalityResults(mappedResults);
          setShowNationalityResults(true);
          message.success(`Nationality classification completed! Classified ${mappedResults.length} profiles. They have been saved to Leads.`);
        } else {
          message.success('Nationality classification started successfully!');
        }
      } catch (error) {
        console.error('Error starting nationality classification:', error);
        message.error('Failed to start nationality classification');
      } finally {
        setLoading(false);
      }
    };

    return (
      <Card>
        <Title level={3}>
          <FlagOutlined /> Nationality Classification
        </Title>
        <Text type="secondary">
          Classify profiles by nationality based on bio and content
        </Text>
        
        {/* Warning Message */}
        <div style={{ 
          marginTop: 16, 
          padding: 12, 
          backgroundColor: '#fff2e8', 
          border: '1px solid #ffb366', 
          borderRadius: 6 
        }}>
          <Text style={{ color: '#d46b08', fontWeight: 'bold' }}>
            ⚠️ Warning: Nationality information are not %100 correct. Please check results.
          </Text>
        </div>
        
        {/* Debug info */}
        {profileScrapingResults.length > 0 && (
          <div style={{ marginTop: 16, padding: 12, backgroundColor: '#f0f9ff', border: '1px solid #91d5ff', borderRadius: 6 }}>
            <Text type="secondary">
              📊 Profile scraping results available: {profileScrapingResults.length} profiles
            </Text>
            <br />
            <Text type="secondary">
              Profile details (username, full name, bio) will be automatically loaded into the form below.
            </Text>
          </div>
        )}
        
        <div style={{ marginTop: 24 }}>
          {/* Profile Data Table */}
          {profileScrapingResults.length > 0 ? (
            <div>
              <Title level={5}>Profile Data for Nationality Classification</Title>
              <Table
                dataSource={profileScrapingResults}
                columns={[
                  {
                    title: 'Username',
                    dataIndex: 'username',
                    key: 'username',
                    render: (text: string) => <Text strong>@{text}</Text>
                  },
                  {
                    title: 'Full Name',
                    dataIndex: 'full_name',
                    key: 'full_name',
                    render: (text: string) => text || 'N/A'
                  },
                  {
                    title: 'Bio',
                    dataIndex: 'bio',
                    key: 'bio',
                    render: (text: string) => (
                      <Text ellipsis={{ tooltip: text }} style={{ maxWidth: 200 }}>
                        {text || 'No bio'}
                      </Text>
                    )
                  },
                  {
                    title: 'Followers',
                    dataIndex: 'followers_count',
                    key: 'followers_count',
                    render: (count: number) => count?.toLocaleString() || 'N/A'
                  }
                ]}
                pagination={{ pageSize: 5 }}
                scroll={{ y: 200 }}
                size="small"
                style={{ marginBottom: 16 }}
              />
              
              <Form
                form={form}
                layout="vertical"
                onFinish={onFinish}
                style={{ marginTop: 16 }}
              >
                <Form.Item
                  name="session_name"
                  label="Session Name"
                  rules={[{ required: true, message: 'Please enter session name' }]}
                >
                  <Input 
                    placeholder="e.g., Turkish Users, Target Audience, etc."
                    defaultValue={`Nationality Classification - ${new Date().toLocaleString()}`}
                  />
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    icon={<FlagOutlined />}
                    size="large"
                    style={{ width: '100%' }}
                  >
                    Start Nationality Classification
                  </Button>
                </Form.Item>
              </Form>
            </div>
          ) : (
            <Card style={{ textAlign: 'center', padding: '40px' }}>
              <Text type="secondary">
                No profile data available. Please run Profile Scraping first.
              </Text>
            </Card>
          )}
        </div>
        
                      {/* Results Section */}
                      {showNationalityResults && nationalityResults.length > 0 && (
                        <Card style={{ marginTop: 24, backgroundColor: '#fff7e6', border: '1px solid #ffd591' }}>
                          <Title level={4} style={{ color: '#fa8c16' }}>
                            🏳️ Nationality Classification Results
                          </Title>
                          <Text>
                            Classified <strong>{nationalityResults.length}</strong> profiles by nationality.
                          </Text>
                          
                          <div style={{ marginTop: 16 }}>
                            <Table
                              dataSource={nationalityResults}
                              columns={[
                                {
                                  title: 'Username',
                                  dataIndex: 'username',
                                  key: 'username',
                                  render: (text: string) => <Text strong>@{text}</Text>
                                },
                                {
                                  title: 'Full Name',
                                  dataIndex: 'full_name',
                                  key: 'full_name',
                                  render: (text: string) => text || 'N/A'
                                },
                                {
                                  title: 'Bio',
                                  dataIndex: 'bio',
                                  key: 'bio',
                                  render: (text: string) => (
                                    <Text ellipsis={{ tooltip: text }} style={{ maxWidth: 200 }}>
                                      {text || 'No bio'}
                                    </Text>
                                  )
                                },
                                {
                                  title: 'Nationality',
                                  dataIndex: 'nationality',
                                  key: 'nationality',
                                  render: (text: string, record: any) => (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                      <Tag color={text?.includes('TÜRK') ? 'green' : 'orange'}>
                                        {text || 'Unknown'}
                                      </Tag>
                                      <Button 
                                        size="small" 
                                        type="link"
                                        onClick={() => handleNationalityEdit(record)}
                                      >
                                        Edit
                                      </Button>
                                      <Button 
                                        size="small" 
                                        type="link"
                                        onClick={() => handleNationalitySwap(record)}
                                      >
                                        {text?.includes('TÜRK') ? '→ YABANCI' : '→ TÜRK'}
                                      </Button>
                                    </div>
                                  )
                                }
                              ]}
                              pagination={{ pageSize: 10 }}
                              scroll={{ y: 400 }}
                              size="small"
                            />
                          </div>
                        </Card>
                      )}
        
        {/* Nationality Edit Modal */}
        <Modal
          title={`Edit Nationality - @${editingNationality?.username}`}
          open={editModalVisible}
          onCancel={() => {
            setEditModalVisible(false);
            setEditingNationality(null);
          }}
          footer={[
            <Button key="cancel" onClick={() => setEditModalVisible(false)}>
              Cancel
            </Button>,
            <Button 
              key="save" 
              type="primary" 
              onClick={() => {
                console.log('🔍 SAVE BUTTON CLICKED IN CAMPAIGNS!');
                console.log('📊 Editing nationality:', editingNationality);
                
                // Get nationality from input field
                const nationalityInput = document.querySelector('input[name="nationality"]') as HTMLInputElement;
                if (nationalityInput) {
                  const nationality = nationalityInput.value;
                  console.log('📊 Nationality from input:', nationality);
                  handleEditSave({ nationality });
                } else {
                  console.log('❌ Nationality input not found!');
                }
              }}
            >
              Save
            </Button>
          ]}
        >
          {editingNationality && (
            <div>
              <div style={{ marginBottom: 16 }}>
                <Text strong>Current Nationality: </Text>
                <Tag color={editingNationality.nationality?.includes('TÜRK') ? 'green' : 'orange'}>
                  {editingNationality.nationality}
                </Tag>
              </div>
              <div>
                <Text strong>New Nationality:</Text>
                <Input 
                  name="nationality"
                  data-nationality-form
                  placeholder="Enter new nationality (e.g., TÜRK, YABANCI)"
                  defaultValue={editingNationality.nationality}
                  style={{ marginTop: 8 }}
                />
              </div>
            </div>
          )}
        </Modal>
      </Card>
    );
  };

  const MessageTemplatesTab: React.FC = () => {
    const [form] = Form.useForm();
    const [templates, setTemplates] = React.useState([]);
    const [selectedTemplate, setSelectedTemplate] = React.useState(null);
    const [isEditing, setIsEditing] = React.useState(false);

    // Fetch user templates from backend
    React.useEffect(() => {
      if (!isAuthenticated) {
        return;
      }

      const fetchUserTemplates = async () => {
        try {
          const response = await api.get('/message-templates');
          if (response.data.success) {
            setTemplates(response.data.data);
            console.log('📝 User templates loaded:', response.data.data.length);
          }
        } catch (error) {
          console.error('Error fetching user templates:', error);
          message.error('Failed to fetch user templates');
        }
      };
      
      fetchUserTemplates();
    }, [isAuthenticated]);

    const onFinish = async (values: any) => {
      try {
        setLoading(true);
        
        if (isEditing && selectedTemplate) {
          // Update existing template (local state only for now)
          const updatedTemplates = templates.map(t => 
            t.id === selectedTemplate.id 
              ? { ...t, name: values.template_name, content: values.message_content }
              : t
          );
          setTemplates(updatedTemplates);
          message.success('Template updated successfully!');
        } else {
          // Create new template via API
          const response = await api.post('/message-templates', {
            template_name: values.template_name,
            message_content: values.message_content
          });
          
          if (response.data.success) {
            // Refresh templates from backend
            const templatesResponse = await api.get('/message-templates');
            if (templatesResponse.data.success) {
              setTemplates(templatesResponse.data.data);
            }
            message.success('Template created successfully!');
          }
        }
        
        // Keep form inputs filled - don't reset
        // form.resetFields(); // Removed to prevent input clearing
        setSelectedTemplate(null);
        setIsEditing(false);
      } catch (error) {
        console.error('Error saving template:', error);
        message.error('Failed to save template');
      } finally {
        setLoading(false);
      }
    };

    const handleTemplateSelect = (template: any) => {
      console.log('🔍 TEMPLATE SELECTED!');
      console.log('📊 Template:', template);
      setSelectedTemplate(template);
      form.setFieldsValue({
        template_name: template.name,
        message_content: template.content
      });
      console.log('🔍 Form filled with selected template');
    };

    const handleEdit = () => {
      console.log('🔍 EDIT TEMPLATE CLICKED!');
      console.log('📊 Selected template:', selectedTemplate);
      setIsEditing(true);
      
      // Fill form with selected template data
      if (selectedTemplate) {
        console.log('🔍 Filling form with:', selectedTemplate.name, selectedTemplate.content);
        form.setFieldsValue({
          template_name: selectedTemplate.name,
          message_content: selectedTemplate.content
        });
        console.log('🔍 Form filled with template data');
      } else {
        console.log('❌ No selected template!');
      }
    };

    const handleDelete = (templateId: string) => {
      const updatedTemplates = templates.filter(t => t.id !== templateId);
      setTemplates(updatedTemplates);
      message.success('Template deleted successfully!');
    };

    const handleNewTemplate = () => {
      setSelectedTemplate(null);
      setIsEditing(false);
      // Keep form inputs filled - don't reset
    };

    return (
      <div>
        <Card style={{ marginBottom: 24 }}>
          <Title level={3}>
            <MessageOutlined /> Message Templates
          </Title>
          <Text type="secondary">
            Create and manage message templates for campaigns
          </Text>
          
          <Form
            form={form}
            layout="vertical"
            onFinish={onFinish}
            style={{ marginTop: 24 }}
          >
            <Form.Item
              name="template_name"
              label="Template Name"
              rules={[{ required: true, message: 'Please enter template name' }]}
            >
              <Input placeholder="e.g., Welcome Message, Follow-up, etc." />
            </Form.Item>

            <Form.Item
              name="message_content"
              label="Message Content"
              rules={[{ required: true, message: 'Please enter message content' }]}
            >
              <Input.TextArea
                rows={6}
                placeholder="Enter your message template here... Use {username} for dynamic username insertion"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={<MessageOutlined />}
                size="large"
                style={{ marginRight: 8 }}
              >
                {isEditing ? 'Update Template' : 'Create Template'}
              </Button>
              <Button
                onClick={handleNewTemplate}
                size="large"
              >
                New Template
              </Button>
            </Form.Item>
          </Form>
        </Card>

        <Card>
          <Title level={4}>Available Templates</Title>
          <Row gutter={[16, 16]}>
            {templates.map((template) => (
              <Col xs={24} sm={12} md={8} lg={6} key={template.id}>
                <Card
                  size="small"
                  hoverable
                  style={{ 
                    cursor: 'pointer',
                    border: selectedTemplate?.id === template.id ? '2px solid #1890ff' : '1px solid #d9d9d9'
                  }}
                  onClick={() => {
                    console.log('🔍 TEMPLATE CARD CLICKED!');
                    console.log('📊 Template:', template);
                    handleTemplateSelect(template);
                  }}
                  actions={[
                    <Button 
                      type="link" 
                      size="small" 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEdit();
                      }}
                    >
                      Edit
                    </Button>,
                    <Button 
                      type="link" 
                      size="small" 
                      danger
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(template.id);
                      }}
                    >
                      Delete
                    </Button>
                  ]}
                >
                  <Card.Meta
                    title={template.name}
                    description={
                      <div>
                        <Text ellipsis={{ tooltip: template.content }}>
                          {template.content}
                        </Text>
                      </div>
                    }
                  />
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      </div>
    );
  };

  const MessageCampaignTab: React.FC = () => {
    const [form] = Form.useForm();
    const [campaignType, setCampaignType] = React.useState('single');
    const [leads, setLeads] = React.useState([]);
    const [sessions, setSessions] = React.useState([]);
    const [selectedLeads, setSelectedLeads] = React.useState([]);
    const [selectedSession, setSelectedSession] = React.useState('');
    const [selectedNationality, setSelectedNationality] = React.useState('');
    const [instagramAccounts, setInstagramAccounts] = React.useState([]);
    const [templates, setTemplates] = React.useState([]);

    // Filter leads by session and nationality
    const getFilteredLeads = () => {
      return leads.filter(lead => {
        const sessionMatch = !selectedSession || lead.session_name === selectedSession;
        const nationalityMatch = !selectedNationality || 
          (selectedNationality === 'turkish' && lead.nationality && lead.nationality.includes('TÜRK')) ||
          (selectedNationality === 'foreign' && lead.nationality && lead.nationality.includes('YABANCI'));
        return sessionMatch && nationalityMatch;
      });
    };

    // Select All functionality
    const handleSelectAll = () => {
      const filteredLeads = getFilteredLeads();
      const maxLeads = Math.min(100, filteredLeads.length);
      const leadsToSelect = filteredLeads.slice(0, maxLeads);
      setSelectedLeads(leadsToSelect);
      
      if (filteredLeads.length > 100) {
        message.warning(`Selected first 100 leads out of ${filteredLeads.length} available`);
      } else {
        message.success(`Selected all ${leadsToSelect.length} leads`);
      }
    };

    const handleDeselectAll = () => {
      setSelectedLeads([]);
      message.success('Deselected all leads');
    };

    // Fetch user-specific data on component mount
    React.useEffect(() => {
      if (!isAuthenticated) {
        return;
      }

      const fetchUserData = async () => {
        try {
          const [leadsResponse, sessionsResponse, accountsResponse, templatesResponse] = await Promise.all([
            api.get('/leads'),
            api.get('/leads/sessions'),
            api.get('/instagram-accounts'),
            api.get('/message-templates')
          ]);
          
          if (leadsResponse.data.success) {
            setLeads(leadsResponse.data.data);
            console.log('📋 User leads loaded:', leadsResponse.data.data.length);
          }
          
          if (sessionsResponse.data.success) {
            setSessions(sessionsResponse.data.data);
            console.log('📊 User sessions loaded:', sessionsResponse.data.data.length);
          }
          
          if (accountsResponse.data.success) {
            setInstagramAccounts(accountsResponse.data.data);
            console.log('🔐 User Instagram accounts loaded:', accountsResponse.data.data.length);
          }
          
          if (templatesResponse.data.success) {
            setTemplates(templatesResponse.data.data);
            console.log('📝 User templates loaded:', templatesResponse.data.data.length);
          }
        } catch (error) {
          console.error('Error fetching user data:', error);
          message.error('Failed to fetch user data');
        }
      };
      
      fetchUserData();
    }, [isAuthenticated]);

    const onFinish = async (values: any) => {
      try {
        setLoading(true);
        
        let usernames = [];
        
        if (campaignType === 'leads') {
          // Use selected leads
          if (selectedLeads.length === 0) {
            message.error('Please select at least one lead');
            setLoading(false);
            return;
          }
          usernames = selectedLeads.map(lead => lead.username);
          console.log('📋 Selected leads:', selectedLeads.length);
          console.log('👥 Usernames from leads:', usernames);
        } else if (campaignType === 'single') {
          // Single message - use single username
          usernames = [values.single_username];
        } else {
          // Bulk campaign - parse usernames from textarea
          usernames = values.target_usernames 
            ? values.target_usernames.split('\n').filter((u: string) => u.trim())
            : [];
        }
        
        // Prepare request data according to backend model
        const requestData = {
          usernames: usernames,
          template_id: values.template_id,
          delay_seconds: values.delay_seconds || 2,
          campaign_type: campaignType,
          instagram_account_id: values.instagram_account_id
        };
        
        console.log('📤 Sending request data:', requestData);
        
        const response = await api.post('/campaigns/message-campaign', requestData);
        
        if (campaignType === 'leads') {
          message.success(`Message campaign started for ${usernames.length} leads!`);
        } else if (campaignType === 'single') {
          message.success('Message sent successfully!');
        } else {
          message.success('Message campaign started successfully!');
        }
        
        // Keep form inputs filled - don't reset
      } catch (error) {
        console.error('Error sending message:', error);
        message.error('Failed to send message');
      } finally {
        setLoading(false);
      }
    };

    return (
      <Card>
        <Title level={3}>
          <SendOutlined /> Message Campaign
        </Title>
        <Text type="secondary">
          Send messages to target profiles using templates
        </Text>
        
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          style={{ marginTop: 24 }}
        >
          <Form.Item
            name="campaign_name"
            label="Campaign Name"
            rules={[{ required: true, message: 'Please enter campaign name' }]}
          >
            <Input placeholder="e.g., Welcome Campaign, Follow-up Series, etc." />
          </Form.Item>

          <Form.Item
            name="instagram_account_id"
            label="Instagram Account"
            rules={[{ required: true, message: 'Please select Instagram account' }]}
          >
            <Select placeholder="Select Instagram account">
              {instagramAccounts.map(account => (
                <Option key={account.id} value={account.id}>
                  {account.username}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="template_id"
            label="Message Template"
            rules={[{ required: true, message: 'Please select template' }]}
          >
            <Select placeholder="Select message template">
              {templates.map(template => (
                <Option key={template.id} value={template.id}>
                  {template.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="campaign_type"
            label="Campaign Type"
            rules={[{ required: true, message: 'Please select campaign type' }]}
          >
            <Radio.Group 
              value={campaignType} 
              onChange={(e) => setCampaignType(e.target.value)}
            >
              <Radio value="leads">From Leads</Radio>
              <Radio value="single">Single Message</Radio>
              <Radio value="bulk">Bulk Campaign</Radio>
            </Radio.Group>
          </Form.Item>

          {campaignType === 'leads' ? (
            <div>
              <Form.Item
                name="session_filter"
                label="Filter by Session"
              >
                <Select 
                  placeholder="Select session (optional)"
                  allowClear
                  onChange={(value) => setSelectedSession(value)}
                >
                  {sessions.map(session => (
                    <Option key={session.id} value={session.name}>
                      {session.name} ({session.lead_count} leads)
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="nationality_filter"
                label="Filter by Nationality"
              >
                <Select 
                  placeholder="Select nationality (optional)"
                  allowClear
                  onChange={(value) => setSelectedNationality(value)}
                >
                  <Option value="turkish">🇹🇷 Turkish Only</Option>
                  <Option value="foreign">🌍 Foreign Only</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="selected_leads"
                label="Select Target Leads (Max 100)"
                rules={[
                  { required: true, message: 'Please select at least one lead' },
                  {
                    validator: (_, value) => {
                      if (selectedLeads.length > 100) {
                        return Promise.reject(new Error('Maximum 100 leads allowed'));
                      }
                      return Promise.resolve();
                    }
                  }
                ]}
              >
                <div style={{ maxHeight: 300, overflowY: 'auto', border: '1px solid #d9d9d9', borderRadius: 6, padding: 8 }}>
                  <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      Selected: {selectedLeads.length}/100 leads
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <Button 
                        size="small" 
                        type="primary" 
                        onClick={handleSelectAll}
                        disabled={leads.filter(lead => !selectedSession || lead.session_name === selectedSession).length === 0}
                      >
                        Select All (Max 100)
                      </Button>
                      <Button 
                        size="small" 
                        onClick={handleDeselectAll}
                        disabled={selectedLeads.length === 0}
                      >
                        Deselect All
                      </Button>
                    </div>
                  </div>
                  <Checkbox.Group
                    value={selectedLeads.map(lead => lead.id)}
                    onChange={(checkedValues) => {
                      if (checkedValues.length > 100) {
                        message.error('Maximum 100 leads allowed');
                        return;
                      }
                      const selected = leads.filter(lead => checkedValues.includes(lead.id));
                      setSelectedLeads(selected);
                    }}
                  >
                    <Row gutter={[8, 8]}>
                      {getFilteredLeads().map(lead => (
                          <Col span={24} key={lead.id}>
                            <Card size="small" style={{ margin: '4px 0' }}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                                  <Checkbox value={lead.id} style={{ marginRight: 8 }}>
                                    <div>
                                      <Text strong>@{lead.username}</Text>
                                      <br />
                                      <Text type="secondary">{lead.full_name}</Text>
                                      <br />
                                      <Text type="secondary" style={{ fontSize: '12px' }}>
                                        {lead.followers_count?.toLocaleString()} followers • {lead.nationality} • {lead.session_name}
                                      </Text>
                                    </div>
                                  </Checkbox>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                  {lead.is_verified && <Tag color="blue">Verified</Tag>}
                                  {lead.nationality && (
                                    <Tag color={lead.nationality.includes('TÜRK') ? 'green' : 'orange'}>
                                      {lead.nationality.includes('TÜRK') ? '🇹🇷 TÜRK' : '🌍 YABANCI'}
                                    </Tag>
                                  )}
                                </div>
                              </div>
                            </Card>
                          </Col>
                        ))}
                    </Row>
                  </Checkbox.Group>
                </div>
              </Form.Item>
            </div>
          ) : campaignType === 'single' ? (
            <Form.Item
              name="single_username"
              label="Target Username"
              rules={[{ required: true, message: 'Please enter username' }]}
            >
              <Input placeholder="Enter username (without @)" />
            </Form.Item>
          ) : (
            <Form.Item
              name="target_usernames"
              label="Target Usernames (Max 100)"
              rules={[
                { required: true, message: 'Please enter target usernames' },
                {
                  validator: (_, value) => {
                    if (value) {
                      const usernames = value.split('\n').filter((u: string) => u.trim());
                      if (usernames.length > 100) {
                        return Promise.reject(new Error('Maximum 100 usernames allowed'));
                      }
                    }
                    return Promise.resolve();
                  }
                }
              ]}
            >
              <TextArea
                rows={6}
                placeholder="username1&#10;username2&#10;username3&#10;...&#10;(Maximum 100 usernames)"
              />
            </Form.Item>
          )}

          <Form.Item
            name="delay_seconds"
            label="Delay Between Messages (seconds)"
            initialValue={5}
          >
            <InputNumber 
              min={1} 
              max={60} 
              placeholder="5" 
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<SendOutlined />}
              size="large"
            >
              {campaignType === 'leads' ? `Send Messages to ${selectedLeads.length} Leads` : 
               campaignType === 'single' ? 'Send Message' : 'Start Message Campaign'}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    );
  };

  const tabItems = [
    {
      key: 'location',
      label: (
        <span>
          <EnvironmentOutlined />
          Location Scraping
        </span>
      ),
      children: <LocationScrapingTab />,
    },
    {
      key: 'upload',
      label: (
        <span>
          <UploadOutlined />
          Upload Profiles
        </span>
      ),
      children: <UploadProfilesTab />,
    },
    {
      key: 'profile',
      label: (
        <span>
          <UserOutlined />
          Profile Scraping
        </span>
      ),
      children: <ProfileScrapingTab />,
    },
    {
      key: 'nationality',
      label: (
        <span>
          <FlagOutlined />
          Nationality Classification
        </span>
      ),
      children: <NationalityClassificationTab />,
    },
    {
      key: 'templates',
      label: (
        <span>
          <MessageOutlined />
          Message Templates
        </span>
      ),
      children: <MessageTemplatesTab />,
    },
    {
      key: 'campaign',
      label: (
        <span>
          <SendOutlined />
          Message Campaign
        </span>
      ),
      children: <MessageCampaignTab />,
    },
  ];

  return (
    <div style={{ 
      padding: '24px', 
      background: '#ffffff', 
      minHeight: '100vh',
      color: '#000000'
    }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ color: '#000000', margin: 0 }}>
          Campaigns
        </Title>
        <Text style={{ color: '#666666' }}>
          Manage your Instagram scraping and messaging campaigns
        </Text>
      </div>

      <Tabs
        defaultActiveKey="location"
        items={tabItems}
        size="large"
        style={{
          background: '#ffffff',
        }}
        tabBarStyle={{
          background: '#f5f5f5',
          borderRadius: '8px 8px 0 0',
          margin: 0,
        }}
      />
    </div>
  );
};

export default Campaigns;