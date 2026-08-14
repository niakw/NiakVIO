#!/usr/bin/env bash
set -euxo pipefail

export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$ANDROID_HOME}"
export ANDROID_USER_HOME="$HOME/.android"
export ANDROID_AVD_HOME="$ANDROID_USER_HOME/avd"
unset ANDROID_SDK_HOME || true
mkdir -p "$ANDROID_AVD_HOME"

SDKMANAGER="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager"
AVDMANAGER="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/avdmanager"
export PATH="$ANDROID_SDK_ROOT/platform-tools:$ANDROID_SDK_ROOT/emulator:$(dirname "$SDKMANAGER"):$PATH"
echo "$ANDROID_SDK_ROOT/platform-tools" >> "$GITHUB_PATH"

yes | "$SDKMANAGER" --licenses >/dev/null || true
TV_IMAGE="system-images;android-34;android-tv;x86"
"$SDKMANAGER" "platform-tools" "emulator" "$TV_IMAGE"
echo no | "$AVDMANAGER" create avd \
  --force \
  --name niakvio-tv-ci \
  --package "$TV_IMAGE" \
  --device "tv_1080p" \
  --path "$ANDROID_AVD_HOME/niakvio-tv-ci.avd"

"$ANDROID_SDK_ROOT/emulator/emulator" -list-avds | grep -Fx niakvio-tv-ci
sudo chmod 666 /dev/kvm
"$ANDROID_SDK_ROOT/emulator/emulator" -accel-check
adb kill-server || true
adb start-server

rm -f /tmp/niakvio-tv-emulator.log
nohup "$ANDROID_SDK_ROOT/emulator/emulator" \
  -avd niakvio-tv-ci \
  -port 5556 \
  -no-window \
  -no-audio \
  -no-boot-anim \
  -no-snapshot \
  -wipe-data \
  -gpu swiftshader_indirect \
  -accel on \
  -cores 2 \
  -memory 2048 \
  >/tmp/niakvio-tv-emulator.log 2>&1 &
EMU_PID=$!

SERIAL=""
for attempt in $(seq 1 90); do
  if ! kill -0 "$EMU_PID" 2>/dev/null; then
    echo "TV emulator exited before adb registration" >&2
    cat /tmp/niakvio-tv-emulator.log >&2 || true
    exit 1
  fi
  SERIAL=$(adb devices | awk '$1 ~ /^emulator-/ && ($2 == "device" || $2 == "offline") {print $1; exit}')
  if [ -n "$SERIAL" ]; then break; fi
  sleep 2
done
if [ -z "$SERIAL" ]; then
  echo "TV emulator did not register with adb" >&2
  cat /tmp/niakvio-tv-emulator.log >&2 || true
  exit 1
fi

for attempt in $(seq 1 90); do
  if ! kill -0 "$EMU_PID" 2>/dev/null; then
    echo "TV emulator exited during boot" >&2
    cat /tmp/niakvio-tv-emulator.log >&2 || true
    exit 1
  fi
  STATE=$(adb -s "$SERIAL" get-state 2>/dev/null || true)
  BOOT=$(adb -s "$SERIAL" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)
  echo "tv boot attempt=$attempt state=$STATE completed=$BOOT"
  if [ "$STATE" = "device" ] && [ "$BOOT" = "1" ]; then break; fi
  sleep 2
done

STATE=$(adb -s "$SERIAL" get-state 2>/dev/null || true)
BOOT=$(adb -s "$SERIAL" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)
if [ "$STATE" != "device" ] || [ "$BOOT" != "1" ]; then
  echo "TV emulator failed to boot" >&2
  cat /tmp/niakvio-tv-emulator.log >&2 || true
  exit 1
fi

CHARACTERISTICS=$(adb -s "$SERIAL" shell getprop ro.build.characteristics | tr -d '\r')
DEVICE_NAME=$(adb -s "$SERIAL" shell getprop ro.product.device | tr -d '\r')
FEATURES=$(adb -s "$SERIAL" shell pm list features | tr -d '\r')
echo "TV characteristics=$CHARACTERISTICS device=$DEVICE_NAME serial=$SERIAL"
printf '%s\n' "$FEATURES" | grep -E 'android\.software\.leanback|android\.hardware\.type\.television' || true
if ! printf '%s\n' "$FEATURES" | grep -Eq 'android\.software\.leanback|android\.hardware\.type\.television'; then
  echo "Android image lacks Leanback/television system feature" >&2
  printf '%s\n' "$FEATURES" >&2
  exit 1
fi

echo "ANDROID_SERIAL=$SERIAL" >> "$GITHUB_ENV"
adb -s "$SERIAL" logcat -c
adb devices -l
