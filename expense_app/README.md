# Expense AI — Mobile App

A mobile-friendly rebuild of your `ass3.py` expense tracker. Same chatbot commands, budget
alerts, search, date filters, and pie chart — now with a touch UI (buttons + chat) instead
of a desktop-only Tkinter window.

**No paid APIs or services are used anywhere.** Everything runs locally on your phone;
storage is a local JSON file on the device.

---

## Files in this project

- `main.py` — the mobile UI (Kivy)
- `logic.py` — your original expense/chatbot logic, ported as-is
- `buildozer.spec` — tells Buildozer how to package the app into an Android APK
- `.github/workflows/build.yml` — a free GitHub Actions workflow that builds the APK
  in the cloud, so **you don't need Android Studio installed on your computer**

---

## The simplest path: build the APK for free using GitHub (no local Android setup)

Buildozer (the tool that turns Python into an Android app) only works properly on
Linux, and setting it up locally is fiddly. The easiest way around this is to let
GitHub build it for you for free, using GitHub's servers. You just need a free
GitHub account.

### Step 1 — Create a free GitHub account
Go to https://github.com and sign up if you don't already have an account.

### Step 2 — Create a new repository
1. Click the **+** icon (top right) → **New repository**
2. Name it something like `expense-ai-app`
3. Set it to **Public** (required for free Actions minutes) or Private (also free, just uses your monthly quota)
4. Click **Create repository**

### Step 3 — Upload the project files
On the new repo page:
1. Click **Add file → Upload files**
2. Drag in `main.py`, `logic.py`, and `buildozer.spec`
3. For the workflow file, GitHub requires the exact folder path `.github/workflows/build.yml`.
   Easiest way: click **Add file → Create new file**, and for the filename type:
   `.github/workflows/build.yml`
   (GitHub will auto-create the folders) — then paste in the workflow file content.
4. Commit the files (click **Commit changes**) each time.

### Step 4 — Run the build
1. Go to the **Actions** tab of your repo
2. You should see "Build Android APK" listed. Click it.
3. Click **Run workflow** → **Run workflow** (green button)
4. Wait — the first build takes **20–40 minutes** (it's compiling Python for Android
   from scratch). You can close the tab and check back later.

### Step 5 — Download your APK
1. Once the run finishes (green checkmark), click into that run
2. Scroll down to **Artifacts**
3. Download `expense-ai-apk` — it's a zip containing your `.apk` file

### Step 6 — Install it on your phone
1. Transfer the `.apk` file to your Android phone (email it to yourself, use Google
   Drive, or a USB cable)
2. On your phone, tap the `.apk` file to install it
3. Android will warn about "unknown sources" — go to **Settings → Security** (or it
   will prompt you directly) and allow installation from that source
4. Open the app — you're done!

> **Note:** This produces an **Android** APK. Building for **iOS** requires a Mac
> with Xcode and an Apple Developer account (Apple doesn't allow free cloud builds
> the way Android does), so iOS isn't realistically "simplest setup" — if you need
> iOS later, let me know and I'll walk you through that separately.

---

## Alternative: test instantly without building an APK (optional, for quick checks)

If you want to see the app running before committing to the 30-minute cloud build,
you can run it on your **computer** first (not your phone) to sanity-check the UI:

```bash
pip install kivy matplotlib
python main.py
```

This opens a desktop window simulating the phone screen. It won't be "on your phone,"
but it confirms everything works before you build the real APK.

---

## How the app works (quick tour)

- **Buttons row** at the top: Expenses, Summary, Today, Month, Budget, Graph, Clear All
- **Chat box** below: type natural commands just like before, e.g.:
  - `spent 500 on food`
  - `show`
  - `summary`
  - `search food`
  - `edit 2 to 600`
  - `delete 1`
  - `set budget 5000`
  - `today` / `this month`
- Data is saved locally in the app's private storage folder on your phone — it
  persists between app launches, nothing is sent anywhere.

---

## If something goes wrong in the build

- **Build fails on first run**: Buildozer/Android toolchain steps sometimes fail on
  a fresh run due to a license prompt timing issue — just click **Run workflow**
  again; second runs are usually faster and more reliable since dependencies are cached.
- **"gradle" or "NDK" errors**: These are almost always fixed by re-running the
  workflow — the Android SDK/NDK download can occasionally time out on GitHub's servers.
- Paste me the exact error text from the Actions log and I'll help you fix the
  `buildozer.spec` or workflow file.
