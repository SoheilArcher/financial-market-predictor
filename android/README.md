# Market AI Android

This is a lightweight native Android WebView wrapper for the Market AI dashboard.

Dashboard URL:

```text
http://51.83.160.143:8000/app
```

Build with Android Studio:

1. Open the `android/` folder.
2. Let Android Studio sync Gradle.
3. Run the `app` configuration on a device or emulator.
4. To build an APK, use `Build > Build Bundle(s) / APK(s) > Build APK(s)`.

Command line, if Android SDK and Gradle are installed:

```bash
cd android
gradle :app:assembleDebug
```

The debug APK will be created under:

```text
android/app/build/outputs/apk/debug/
```
