#!/usr/bin/env bash
# Runs on the macOS GitHub runner right after `npx cap add ios` (before `cap sync`).
# Makes the Xcode project App Store-ready:
#  - Info.plist: AdMob app id, Apple's "Allow tracking?" text, SKAdNetwork ids, photo-saving text,
#    portrait only, full screen / no status bar, no export-compliance question, version + build number,
#    Google sign-in URL scheme (when Firebase is set up)
#  - Sign in with Apple entitlement (when Firebase is set up)
#  - PrivacyInfo.xcprivacy (Apple's privacy manifest) + GoogleService-Info.plist added to the app target
set -euo pipefail

PLIST="ios/App/App/Info.plist"
PB=/usr/libexec/PlistBuddy

ADMOB_IOS_APP_ID="$(node -e "
global.window={};require('./www/ads-config.js');
process.stdout.write((window.FLOWER_ADS_IOS||{}).appId||'ca-app-pub-3940256099942544~1458002511');")"

set_value() { # key type value
  if $PB -c "Print :$1" "$PLIST" >/dev/null 2>&1; then $PB -c "Set :$1 $3" "$PLIST"; else $PB -c "Add :$1 $2 $3" "$PLIST"; fi
}

set_value CFBundleDisplayName string "Flower Fever"
set_value GADApplicationIdentifier string "$ADMOB_IOS_APP_ID"
set_value NSUserTrackingUsageDescription string "Flower Fever uses this to show you more relevant ads. Ads keep the game free to play."
set_value NSPhotoLibraryAddUsageDescription string "Flower Fever saves your bouquet and garden pictures to your Photos."
set_value NSPhotoLibraryUsageDescription string "Flower Fever saves your bouquet and garden pictures to your Photos."
set_value ITSAppUsesNonExemptEncryption bool false
set_value UIRequiresFullScreen bool true
set_value UIStatusBarHidden bool true
set_value UIViewControllerBasedStatusBarAppearance bool false

for KEY in UISupportedInterfaceOrientations "UISupportedInterfaceOrientations~ipad"; do
  $PB -c "Delete :$KEY" "$PLIST" >/dev/null 2>&1 || true
  $PB -c "Add :$KEY array" "$PLIST"
  $PB -c "Add :$KEY:0 string UIInterfaceOrientationPortrait" "$PLIST"
done

# SKAdNetwork ids for Google AdMob (Google's list)
$PB -c "Delete :SKAdNetworkItems" "$PLIST" >/dev/null 2>&1 || true
$PB -c "Add :SKAdNetworkItems array" "$PLIST"
i=0
for ID in cstr6suwn9 4fzdc2evr5 2fnua5tdw4 ydx93a7ass p78axxw29g v72qych5uu ludvb6z3bs \
          cp8zw746q7 3sh42y64q3 c6k4g5qg8m s39g8k73mm 3qy4746246 hs6bdukanm mlmmfzh3r3 \
          v4nxqhlyqp wzmmz9fp6w su67r6k2v3 yclnxrl5pm 7ug5zh24hu gta9lk7p23 vutu7akeur \
          y5ghdn5j9k v9wttpbfk9 n38lu8286q 47vhws6wlr kbd757ywx3 9t245vhmpl a2p9lx4jpn \
          22mmun2rn5 44jx6755aq k674qkevps 4468km3ulz 2u9pt9hc89 8s468mfl3y klf5c3l5u5 \
          ppxm28t8ap kbmxgpxpgc uw77j35x4d 578prtvx9j 4dzt52r2t5 tl55sbb4fm e5fvkxwrpn \
          8c4e2ghe7u 3rd42ekr43 3qcr597p9d; do
  $PB -c "Add :SKAdNetworkItems:$i dict" "$PLIST"
  $PB -c "Add :SKAdNetworkItems:$i:SKAdNetworkIdentifier string ${ID}.skadnetwork" "$PLIST"
  i=$((i+1))
done

set_value CFBundleShortVersionString string "${IOS_APP_VERSION:-1.0.0}"
set_value CFBundleVersion string "${IOS_BUILD_NUMBER:-1}"

FILES_TO_ADD=()

# Apple's privacy manifest for the app itself (the SDKs bring their own)
cat > ios/App/App/PrivacyInfo.xcprivacy <<'XML'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>NSPrivacyTracking</key><true/>
  <key>NSPrivacyTrackingDomains</key><array/>
  <key>NSPrivacyCollectedDataTypes</key>
  <array>
    <dict>
      <key>NSPrivacyCollectedDataType</key><string>NSPrivacyCollectedDataTypeDeviceID</string>
      <key>NSPrivacyCollectedDataTypeLinked</key><false/>
      <key>NSPrivacyCollectedDataTypeTracking</key><true/>
      <key>NSPrivacyCollectedDataTypePurposes</key><array><string>NSPrivacyCollectedDataTypePurposeThirdPartyAdvertising</string></array>
    </dict>
    <dict>
      <key>NSPrivacyCollectedDataType</key><string>NSPrivacyCollectedDataTypeGameplayContent</string>
      <key>NSPrivacyCollectedDataTypeLinked</key><true/>
      <key>NSPrivacyCollectedDataTypeTracking</key><false/>
      <key>NSPrivacyCollectedDataTypePurposes</key><array><string>NSPrivacyCollectedDataTypePurposeAppFunctionality</string></array>
    </dict>
  </array>
  <key>NSPrivacyAccessedAPITypes</key>
  <array>
    <dict>
      <key>NSPrivacyAccessedAPIType</key><string>NSPrivacyAccessedAPICategoryUserDefaults</string>
      <key>NSPrivacyAccessedAPITypeReasons</key><array><string>CA92.1</string></array>
    </dict>
    <dict>
      <key>NSPrivacyAccessedAPIType</key><string>NSPrivacyAccessedAPICategoryFileTimestamp</string>
      <key>NSPrivacyAccessedAPITypeReasons</key><array><string>C617.1</string></array>
    </dict>
  </array>
</dict>
</plist>
XML
FILES_TO_ADD+=("PrivacyInfo.xcprivacy")

if [ -f GoogleService-Info.plist ]; then
  cp GoogleService-Info.plist ios/App/App/GoogleService-Info.plist
  FILES_TO_ADD+=("GoogleService-Info.plist")
  # Google sign-in needs the reversed client id as a URL scheme
  REVERSED="$($PB -c 'Print :REVERSED_CLIENT_ID' GoogleService-Info.plist)"
  $PB -c "Delete :CFBundleURLTypes" "$PLIST" >/dev/null 2>&1 || true
  $PB -c "Add :CFBundleURLTypes array" "$PLIST"
  $PB -c "Add :CFBundleURLTypes:0 dict" "$PLIST"
  $PB -c "Add :CFBundleURLTypes:0:CFBundleURLSchemes array" "$PLIST"
  $PB -c "Add :CFBundleURLTypes:0:CFBundleURLSchemes:0 string $REVERSED" "$PLIST"
  # Sign in with Apple
  cat > ios/App/App/App.entitlements <<'XML'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>com.apple.developer.applesignin</key>
  <array><string>Default</string></array>
</dict>
</plist>
XML
  PBX="ios/App/App.xcodeproj/project.pbxproj"
  if ! grep -q "CODE_SIGN_ENTITLEMENTS" "$PBX"; then
    sed -i '' 's#INFOPLIST_FILE = App/Info.plist;#INFOPLIST_FILE = App/Info.plist;\
				CODE_SIGN_ENTITLEMENTS = App/App.entitlements;#' "$PBX"
  fi
  # Google sign-in + Analytics pods (optional parts of the Firebase plugins)
  ruby - <<'RUBY'
podfile = "ios/App/Podfile"
s = File.read(podfile)
extra = "  pod 'CapacitorFirebaseAuthentication/Google', :path => '../../node_modules/@capacitor-firebase/authentication'\n" \
        "  pod 'CapacitorFirebaseAnalytics/Analytics', :path => '../../node_modules/@capacitor-firebase/analytics'\n"
unless s.include?("CapacitorFirebaseAuthentication/Google")
  s = s.sub(/(target 'App' do\n\s*capacitor_pods\n)/) { $1 + extra }
  File.write(podfile, s)
end
puts File.read(podfile)
RUBY
else
  echo "::notice::No GoogleService-Info.plist yet: the iPhone app builds without sign-in, cloud save, friends and analytics."
fi

# add the files to the App target (Copy Bundle Resources)
ruby - "${FILES_TO_ADD[@]}" <<'RUBY'
require 'xcodeproj'
proj = Xcodeproj::Project.open('ios/App/App.xcodeproj')
target = proj.targets.find { |t| t.name == 'App' }
group = proj.main_group.find_subpath('App', false)
ARGV.each do |name|
  next if group.files.any? { |f| f.path == name }
  ref = group.new_reference(name)
  target.add_resources([ref])
  puts "added #{name} to the App target"
end
proj.save
RUBY

echo "Info.plist:"; $PB -c "Print" "$PLIST" | grep -E "GADApplicationIdentifier|NSUserTracking|CFBundleShortVersion|CFBundleVersion|NSPhotoLibraryAdd" || true
