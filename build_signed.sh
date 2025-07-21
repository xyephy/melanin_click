#!/bin/bash

# Melanin Click - Signed Build Script for macOS
# This script builds and signs the app for distribution

set -e

echo "🏗️  Building Melanin Click for macOS..."

# Change to the Tauri project directory
cd melanin_click_tauri

# Check if signing identity is set
if [ -z "$APPLE_SIGNING_IDENTITY" ]; then
    echo "⚠️  Warning: APPLE_SIGNING_IDENTITY not set. Using ad-hoc signing."
    echo "   For production builds, set: export APPLE_SIGNING_IDENTITY=\"Developer ID Application: Your Name (TEAM_ID)\""
else
    echo "✅ Using signing identity: $APPLE_SIGNING_IDENTITY"
    
    # Update tauri.conf.json with the signing identity
    jq --arg identity "$APPLE_SIGNING_IDENTITY" '.bundle.macOS.signingIdentity = $identity' src-tauri/tauri.conf.json > tmp.json && mv tmp.json src-tauri/tauri.conf.json
fi

# Build the app
echo "🔨 Building the application..."
npm run tauri build

# Find the built app
APP_PATH=$(find src-tauri/target/release/bundle/macos -name "*.app" | head -1)
DMG_PATH=$(find src-tauri/target/release/bundle/dmg -name "*.dmg" | head -1)

if [ -n "$APP_PATH" ] && [ -n "$DMG_PATH" ]; then
    echo "✅ Build completed successfully!"
    echo "   App: $APP_PATH"
    echo "   DMG: $DMG_PATH"
    
    # If we have a signing identity, also notarize
    if [ -n "$APPLE_SIGNING_IDENTITY" ] && [ -n "$APPLE_ID" ] && [ -n "$APPLE_PASSWORD" ]; then
        echo "📝 Notarizing the app..."
        xcrun notarytool submit "$DMG_PATH" --apple-id "$APPLE_ID" --password "$APPLE_PASSWORD" --team-id "$APPLE_TEAM_ID" --wait
        echo "✅ Notarization complete!"
    fi
else
    echo "❌ Build failed - could not find output files"
    exit 1
fi

echo "🎉 Build process completed!"
echo ""
echo "📦 Distribution files:"
echo "   - App bundle: $APP_PATH"
echo "   - DMG installer: $DMG_PATH"
echo ""
echo "🔒 Security status:"
if [ -n "$APPLE_SIGNING_IDENTITY" ]; then
    echo "   - Code signed: ✅"
    if [ -n "$APPLE_ID" ]; then
        echo "   - Notarized: ✅"
    else
        echo "   - Notarized: ❌ (set APPLE_ID and APPLE_PASSWORD for notarization)"
    fi
else
    echo "   - Code signed: ❌ (development build)"
    echo "   - Notarized: ❌"
fi 