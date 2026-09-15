# Mobile Dev Environment Setup (Arch Linux)

Install these before the next session so the Android app can be scaffolded and
built/verified locally. Everything below is host-level tooling for the mobile
half of Phase 2 only — it does not touch the daemon (which stays container-first).

## 1. JDK 17 (required by Android Gradle Plugin 8.x)

```bash
sudo pacman -S jdk17-openjdk
```

Confirm it's the default JVM:

```bash
archlinux-java status
```

If JDK 17 isn't the default, set it:

```bash
sudo archlinux-java set java-17-openjdk
```

Check: `java -version` should show `openjdk version "17..."`.

## 2. Android SDK (command-line tools)

We don't need Android Studio to build — just the command-line tools + SDK.

```bash
mkdir -p ~/Android/Sdk/cmdline-tools
cd ~/Android/Sdk/cmdline-tools
curl -L -o tools.zip \
  "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
unzip -q tools.zip
rm tools.zip
mv cmdline-tools latest   # dir must be named 'latest'
```

## 3. Install SDK packages + accept licenses

```bash
export ANDROID_HOME=~/Android/Sdk
export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin"

# platform-tools (adb), the platform + build-tools we'll pin in Gradle, emulator deps omitted
yes | sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-35" "build-tools;34.0.0"
```

Verify:

```bash
adb --version | head -1
```

## 4. Persistent env vars

Add to `~/.bashrc` (or `~/.zshrc`):

```bash
export ANDROID_HOME=$HOME/Android/Sdk
export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools"
```

Reload: `source ~/.bashrc`.

## 5. Gradle

The repo will ship a Gradle wrapper (`./gradlew`), so a system-wide Gradle is
**not required** — the wrapper downloads its own pinned version on first run.
If you want it anyway for convenience:

```bash
sudo pacman -S gradle
```

## 6. (Optional) Device / Emulator

- **Physical device**: enable Developer options + USB debugging, then
  `./gradlew :app:installDebug` installs straight to the phone.
- **Emulator** (heavier, not required for compile verification):

```bash
sudo pacman -S qemu-system-x86
sdkmanager "emulator" "system-images;android-35;google_apis;x86_64"
avdmanager create avd -n kaow -k "system-images;android-35;google_apis;x86_64"
```

## Quick self-check before next session

```bash
java -version                 # 17
adb --version                 # platform-tools present
ls $ANDROID_HOME              # cmdline-tools, platforms, build-tools
ls $ANDROID_HOME/cmdline-tools/latest/bin | head    # sdkmanager, avdmanager
```

If all four pass, the mobile skeleton can be generated and compile-verified locally.