# Lambda Deployment Quick Reference

## 🚀 Quick Deploy Commands

```bash
# First time
./deploy.sh

# Subsequent deployments
./deploy.sh

# Local testing
sam local start-api

# View logs
sam logs -n WealthCraftAPI --tail
```

## 📝 Environment Variables Needed

From your `.env` file, you'll need:
- `DATABASE_URL` - Supabase connection string
- `SUPABASE_JWT_SECRET` - From Supabase → Settings → API
- `SECRET_KEY` - Generate: `python -c "import secrets; print(secrets.token_hex(32))"`
- `CORS_ORIGINS` - Comma-separated domains (or `*` for dev)

## 🔍 Common Issues

### Import Error
```bash
sam build --use-container
sam deploy
```

### Database Timeout
- Check DATABASE_URL uses pooler (port 6543)
- Verify Supabase allows external connections

### Slow Cold Starts
- Increase MemorySize in template.yaml (512 → 1024)
- Review .samignore to exclude unnecessary files

## 💰 Cost Calculator

```
Monthly requests: ___________
Free tier: 1,000,000
Billable: (requests - 1M)
Cost: billable × $0.20 / 1M = $_____
```

## 📊 Key Metrics to Monitor

- **Invocations**: Total requests
- **Duration**: Response time (target: <1s warm, <3s cold)
- **Errors**: Should be <1%
- **Throttles**: Should be 0

## 🔗 Useful Links

- CloudWatch Logs: `/aws/lambda/wealthcraft-api-WealthCraftAPI-*`
- Lambda Console: AWS Console → Lambda → Functions
- API Gateway: AWS Console → API Gateway
- Billing: AWS Console → Billing Dashboard
