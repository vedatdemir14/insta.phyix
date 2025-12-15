/**
 * Kullanıcının IP adresini tespit etmek için utility fonksiyonları
 */

export interface IPDetectionResult {
  ip: string;
  country?: string;
  city?: string;
  isp?: string;
}

/**
 * Kullanıcının IP adresini tespit et
 * Birden fazla servis dener, ilk başarılı olanı döndürür
 */
export const detectUserIP = async (): Promise<IPDetectionResult> => {
  const services = [
    {
      url: 'https://api.ipify.org?format=json',
      parser: (data: any) => ({ ip: data.ip })
    },
    {
      url: 'https://api.myip.com',
      parser: (data: any) => ({ ip: data.ip })
    },
    {
      url: 'https://ipapi.co/json/',
      parser: (data: any) => ({
        ip: data.ip,
        country: data.country_name,
        city: data.city,
        isp: data.org
      })
    },
    {
      url: 'https://ip-api.com/json/',
      parser: (data: any) => ({
        ip: data.query,
        country: data.country,
        city: data.city,
        isp: data.isp
      })
    }
  ];

  for (const service of services) {
    try {
      const response = await fetch(service.url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        continue;
      }

      const data = await response.json();
      const result = service.parser(data);

      if (result.ip) {
        console.log(`✅ IP detected via ${service.url}:`, result);
        return result;
      }
    } catch (error) {
      console.warn(`⚠️ IP detection failed for ${service.url}:`, error);
      continue;
    }
  }

  throw new Error('Could not detect user IP address from any service');
};




