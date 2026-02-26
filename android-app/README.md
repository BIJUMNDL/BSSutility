# BSS Utility Mobile (Java)

This Android app is intentionally scoped to only:
- Inspection Entry (`/new/`)
- Diesel Filling (`/diesel/new/`)
- Migrations (`/transmedia/migrations/`)

It uses a native Java shell + WebView, reusing your existing Django forms and migration flows.

## 1) Set backend URL
Default backend URL is configured in `app/build.gradle`:
- `buildConfigField "String", "BASE_URL", '"http://10.0.2.2:8000"'`

Use one of these:
- Android Emulator + local Django: `http://10.0.2.2:8000`
- Physical device + same LAN: `http://<PC_LAN_IP>:8000`

## 2) Backend run
From project root:
```powershell
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

## 3) Build debug APK
From `android-app` folder:
```powershell
.\gradlew.bat assembleDebug
```
APK output:
- `app\build\outputs\apk\debug\app-debug.apk`

## 4) Build installation-ready release APK
Create signing key once:
```powershell
keytool -genkeypair -v -keystore bssutility-release.keystore -alias bssutility -keyalg RSA -keysize 2048 -validity 10000
```

Then in Android Studio:
- Build > Generate Signed Bundle / APK > APK
- Select keystore and passwords
- Build `release`

Release APK output:
- `app\build\outputs\apk\release\app-release.apk`

## Notes
- Migrations pages in Django are `@login_required`; user will login through the web page inside app.
- Cleartext HTTP is enabled for LAN/local deployments (`usesCleartextTraffic=true`). For production, use HTTPS.
