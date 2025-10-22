# SSL Certificate Setup for newcf3.cloudfuze.com

## Prerequisites

1. **DNS Configuration**: Ensure your domain `newcf3.cloudfuze.com` points to IP `64.227.160.206`
2. **Server Access**: SSH access to your Ubuntu server
3. **Domain Verification**: The domain must be accessible from the internet

## Method 1: Automatic Setup (Recommended)

The deployment script will automatically set up SSL certificates using Let's Encrypt. Just run:

```bash
chmod +x deploy-ubuntu.sh
./deploy-ubuntu.sh
```

## Method 2: Manual SSL Setup

If you need to set up SSL manually or renew certificates:

### Step 1: Install Certbot

```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

### Step 2: Stop Nginx (if running)

```bash
sudo systemctl stop nginx
# or if using Docker:
docker-compose -f docker-compose.prod.yml stop nginx
```

### Step 3: Get SSL Certificate

```bash
sudo certbot certonly --standalone -d newcf3.cloudfuze.com --non-interactive --agree-tos --email admin@cloudfuze.com
```

### Step 4: Verify Certificate

```bash
sudo certbot certificates
```

### Step 5: Test Certificate Renewal

```bash
sudo certbot renew --dry-run
```

## Method 3: Using Nginx Plugin (Alternative)

If you prefer to use the nginx plugin:

```bash
sudo certbot --nginx -d newcf3.cloudfuze.com --non-interactive --agree-tos --email admin@cloudfuze.com
```

## Certificate Renewal

### Automatic Renewal

Certbot automatically sets up a cron job for renewal. Check with:

```bash
sudo crontab -l
```

### Manual Renewal

```bash
sudo certbot renew
```

### Renewal with Docker

If using Docker, you may need to stop containers during renewal:

```bash
# Create renewal script
sudo tee /etc/cron.d/certbot-renewal > /dev/null << 'EOF'
0 12 * * * root cd /opt/slack2teams && docker-compose -f docker-compose.prod.yml stop nginx && certbot renew --quiet && docker-compose -f docker-compose.prod.yml start nginx
EOF
```

## Troubleshooting

### Common Issues

1. **Domain not pointing to server**:
   ```bash
   nslookup newcf3.cloudfuze.com
   ```

2. **Port 80/443 blocked**:
   ```bash
   sudo ufw status
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. **Certificate not found**:
   ```bash
   sudo ls -la /etc/letsencrypt/live/newcf3.cloudfuze.com/
   ```

4. **Nginx configuration error**:
   ```bash
   sudo nginx -t
   ```

### Testing SSL

```bash
# Test SSL certificate
openssl s_client -connect newcf3.cloudfuze.com:443 -servername newcf3.cloudfuze.com

# Test with curl
curl -I https://newcf3.cloudfuze.com

# Test SSL rating (external)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=newcf3.cloudfuze.com
```

## Security Best Practices

1. **Strong SSL Configuration**: The nginx configuration includes modern SSL settings
2. **HSTS Headers**: Strict Transport Security headers are included
3. **Security Headers**: XSS protection, content type options, etc.
4. **Regular Updates**: Keep certificates and nginx updated

## Monitoring

### Certificate Expiry Monitoring

```bash
# Check certificate expiry
echo | openssl s_client -servername newcf3.cloudfuze.com -connect newcf3.cloudfuze.com:443 2>/dev/null | openssl x509 -noout -dates

# Set up monitoring script
sudo tee /usr/local/bin/check-ssl-expiry.sh > /dev/null << 'EOF'
#!/bin/bash
DOMAIN="newcf3.cloudfuze.com"
EXPIRY=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_LEFT=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))

if [ $DAYS_LEFT -lt 30 ]; then
    echo "WARNING: SSL certificate for $DOMAIN expires in $DAYS_LEFT days"
    # Add email notification here if needed
fi
EOF

sudo chmod +x /usr/local/bin/check-ssl-expiry.sh

# Add to crontab
echo "0 9 * * * /usr/local/bin/check-ssl-expiry.sh" | sudo crontab -
```

## Backup and Recovery

### Backup Certificates

```bash
sudo tar -czf ssl-backup-$(date +%Y%m%d).tar.gz /etc/letsencrypt/
```

### Restore Certificates

```bash
sudo tar -xzf ssl-backup-YYYYMMDD.tar.gz -C /
```

## Support

If you encounter issues:

1. Check Certbot logs: `/var/log/letsencrypt/`
2. Check Nginx logs: `/var/log/nginx/`
3. Verify DNS settings
4. Check firewall rules
5. Ensure domain is accessible from internet
