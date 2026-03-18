## Publishing to GitHub

**Repository:** https://github.com/YOUR-USERNAME/YOUR-REPO-NAME

---

### What is GitHub and why use it?

GitHub is a website that stores your code online. It acts as a backup, lets you track changes over time, and makes it easy to share your app with others. Think of it like Google Drive but for code.

---

### What is a .gitignore file and why does it matter?

When you publish to GitHub, every file in your folder gets uploaded — including sensitive files like your API key. A `.gitignore` file is a simple list that tells GitHub "don't upload these files". This protects your API key and keeps private data off the internet.

**The `.gitignore` file is already created** in your project folder. It protects:
- `.env` — your Anthropic API key
- `data/versions/*.json` — your local evaluation results
- `__pycache__/`, `.DS_Store` — system junk files

You do not need to create or edit it — it is already done.

**Note: `.gitignore` is NOT created automatically by Claude Code or GitHub.** You must create it manually at the start of every new project before pushing to GitHub. If you skip this step, private files like your API key could be uploaded publicly.

**If you ever need to create a `.gitignore` from scratch on a new project:**

**Option A — Using VS Code:**
1. Open your project folder in VS Code
2. In the left sidebar, hover over the folder name → click the **New File** icon (looks like a page with a + sign)
3. Name the file exactly `.gitignore` — dot at the start, no spaces, no extension — press Enter
4. The blank file opens in the editor. Type your exclusions directly into it, one per line:

   ```
   ┌─────────────────────────────────────┐
   │ .gitignore                          │
   ├─────────────────────────────────────┤
   │ .env                                │  ← your API key file
   │ data/versions/*.json                │  ← local saved results
   │ __pycache__/                        │  ← Python cache folder
   │ .DS_Store                           │  ← macOS system file
   └─────────────────────────────────────┘
   ```

5. Press **Cmd+S** to save

**Option B — Using Terminal:**
1. Open Terminal and navigate to your project folder:
   ```
   cd /path/to/your/project
   ```
2. Create the file and open it in TextEdit:
   ```
   touch .gitignore && open -e .gitignore
   ```
3. TextEdit opens with a blank file. Type your exclusions one per line (same content as shown above)
4. Save with **Cmd+S** and close TextEdit

Either way, once saved, GitHub will skip everything listed when you push.

---

### What is a personal access token?

GitHub no longer accepts your normal login password when pushing from Terminal. Instead it uses a personal access token — a long string of characters that acts as a secure password just for this purpose.

**How to create one (one time only):**

1. Go to github.com and log in
2. Click your profile photo (top right) → **Settings**
3. Scroll down the left sidebar → click **Developer settings**
4. Click **Personal access tokens** → **Tokens (classic)**
5. Click **Generate new token** → **Generate new token (classic)**
6. Fill in:
   - **Note:** give it a name e.g. `my-project-token`
   - **Expiration:** choose a date (e.g. 12/31/2026)
   - **Scopes:** tick the box next to **repo** — this selects all sub-boxes automatically
7. Scroll to the bottom → click **Generate token**
8. **Copy the token immediately** — it starts with `ghp_...` and GitHub will never show it again after you leave this page
9. Save it somewhere safe — paste it into your Notes app or a password manager

**When Terminal asks for your password**, paste this token. Nothing will appear as you type — that is normal, just press Enter.

**You do not generate a new token every time.** Reuse the same token until it expires. When it expires, go back to the same location and generate a new one.

**Never share your token** or include it in any file that gets uploaded to GitHub.

---

### Step-by-step: pushing to GitHub for the first time

You only do these steps once.

**Before you start, you need:**
- A GitHub account (github.com)
- A personal access token (see instructions above)
- Your project files in a folder on your Mac

**Step 1 — Create an empty repository on GitHub**

1. Go to github.com and log in
2. Click the **+** icon (top right) → **New repository**
3. Fill in:
   - **Repository name:** e.g. `my-project-name`
   - **Visibility:** Public (anyone can see) or Private (only you)
   - Leave **Add README**, **Add .gitignore**, and **Add license** all turned off
4. Click **Create repository**
5. Copy the URL shown on the next page — it looks like `https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git`

**Step 2 — Open a real Terminal window**

- **Option A:** Press **Cmd+Space** → type **Terminal** → press Enter
- **Option B:** Go to the menu bar → **Shell** → **New Window**
- **Option C:** Open **Finder** → **Applications** → **Utilities** → double-click **Terminal**

> Important: do not use the terminal inside Claude Code — Git commands will not run there.

**Step 3 — Run these commands one at a time**

Copy and paste each line into Terminal, press Enter, and wait for it to finish before running the next one.

Replace `/path/to/your/project` with the actual path to your project folder on your Mac:

```
cd /path/to/your/project
```
```
git init
```
```
git add .
```
```
git commit -m "Initial commit"
```

Replace `YOUR-USERNAME` and `YOUR-REPO-NAME` with your actual GitHub username and repository name:

```
git remote set-url origin https://YOUR-USERNAME@github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
```
```
git push -u origin main
```

**Step 4 — Enter your credentials when prompted**

Terminal will ask for:
- **Username:** your GitHub username
- **Password:** paste your personal access token — nothing will appear as you type, that is normal — then press Enter

**Step 5 — Confirm it worked**

Go to `https://github.com/YOUR-USERNAME/YOUR-REPO-NAME` in your browser. You should see all your files. Check that `.env` is **not** listed — if it is missing from the list, your API key is protected correctly.

---

### Publishing future changes

Every time you make changes to the app and want to save them to GitHub:

1. Open a real Terminal window using one of these methods:
   - **Option A:** Press **Cmd+Space**, type **Terminal**, press Enter
   - **Option B:** If Terminal is already open, go to the menu bar → **Shell** → **New Window**
   - **Option C:** Open **Finder** → **Applications** → **Utilities** → double-click **Terminal**

   Do NOT use the terminal inside Claude Code — Git commands will not work there.

2. Run these commands one at a time, replacing `/path/to/your/project` with your actual folder path:

```
cd /path/to/your/project
```
```
git add .
```
```
git commit -m "Brief description of what you changed"
```
```
git push
```

3. When prompted for password, paste your personal access token

That's it — your changes are now saved online.

---

### Sharing the app with someone else

1. Send them your repository link: `https://github.com/YOUR-USERNAME/YOUR-REPO-NAME`
2. They open Terminal and run, replacing `YOUR-USERNAME` and `YOUR-REPO-NAME` with your actual details:

```
git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
```
```
cd YOUR-REPO-NAME
```
```
pip3 install -r requirements.txt
```

3. They create a new `.env` file in the folder with their own Anthropic API key:
   ```
   ANTHROPIC_API_KEY=their-key-here
   ```
4. They double-click `run.command` to launch the app
