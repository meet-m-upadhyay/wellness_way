# 📝 How to Save Secrets in Notion

## What You Have

I've created 3 files with your environment secrets:

1. **`ENVIRONMENT_SECRETS_GUIDE.md`** - Complete detailed guide
2. **`NOTION_SECRETS_TEMPLATE.md`** - Quick copy-paste version
3. **`SECRETS_ONLY.txt`** - Just the raw secrets

---

## 🎯 Recommended: Save in Notion

### Option 1: Quick & Simple (Recommended)

1. Open **`NOTION_SECRETS_TEMPLATE.md`**
2. Copy the entire content
3. Create a new page in Notion
4. Paste the content
5. Set page to **Private** 🔒
6. Bookmark the page for easy access

### Option 2: Detailed Guide

1. Open **`ENVIRONMENT_SECRETS_GUIDE.md`**
2. Copy the entire content
3. Create a new page in Notion
4. Paste the content
5. Set page to **Private** 🔒

### Option 3: Just the Secrets

1. Open **`SECRETS_ONLY.txt`**
2. Copy the content
3. Save in Notion as code block
4. Set page to **Private** 🔒

---

## 🚀 Using Secrets on New Device

When you clone the project on a new device:

1. Open your Notion page with secrets
2. Copy the **Backend .env** section
3. Create `backend/.env` file and paste
4. Copy the **Frontend .env** section
5. Create `frontend/.env` file and paste
6. Follow the setup steps in the Notion page

---

## ⚠️ Important Security Notes

### These Files Are Gitignored

I've added these files to `.gitignore`:
- `ENVIRONMENT_SECRETS_GUIDE.md`
- `NOTION_SECRETS_TEMPLATE.md`
- `SECRETS_ONLY.txt`

They will **NOT** be committed to git.

### Rotate These Keys (They Were Exposed)

Since these keys were in git history, you should rotate them:

1. **Groq API Key**
   - Go to: https://console.groq.com/keys
   - Delete old key
   - Create new key
   - Update in Notion and all `.env` files

2. **Google OAuth Client Secret**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Find your OAuth client
   - Click "Reset Secret"
   - Update in Notion and all `.env` files

3. **JWT Secret Key**
   - Generate new: `python -c "import secrets; print(secrets.token_urlsafe(64))"`
   - Update in Notion and all `.env` files

---

## 📋 Checklist

- [ ] Copy one of the secret files to Notion
- [ ] Set Notion page to Private
- [ ] Bookmark the Notion page
- [ ] Delete the local secret files (optional, they're gitignored)
- [ ] Rotate exposed API keys
- [ ] Test setup on another device to verify it works

---

## 🗑️ After Saving to Notion

You can safely delete these files from your local machine:
```bash
rm ENVIRONMENT_SECRETS_GUIDE.md
rm NOTION_SECRETS_TEMPLATE.md
rm SECRETS_ONLY.txt
rm NOTION_SETUP_INSTRUCTIONS.md
```

They're already gitignored, so they won't be committed anyway.

---

## 💡 Pro Tips

1. **Create a Notion Database** for all your project secrets
2. **Use Notion's code blocks** for better formatting
3. **Add tags** like "secrets", "env", "wellness-way"
4. **Share with team** if needed (but keep it private from public)
5. **Update Notion** whenever you rotate keys

---

## 🔄 Keeping Secrets Updated

When you rotate keys:
1. Update in Notion first
2. Update on all devices where project runs
3. Update in production environment
4. Test thoroughly

---

## 📞 Need Help?

If you have issues:
1. Check `DOCUMENTATION_INDEX.md` in the project
2. Read `docs/PROJECT_DOCUMENTATION.md`
3. Review `QUICK_START.md`

---

**You're all set! Save to Notion and you can run this project anywhere.** 🎉
