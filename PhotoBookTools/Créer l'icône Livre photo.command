#!/bin/sh
# macOS: creates the application "Livre photo" in ~/Applications, which opens Scribus with
# PhotoBookWebGUI. Double-click it, or drop a Scribus book (.sla) on it to open this book.
# Double-click this file in the Finder to create (or update) the application.

here="$(cd "$(dirname "$0")" && pwd)"
script="$here/PhotoBookWebGUI.py"
app="$HOME/Applications/Livre photo.app"

# the Scribus to use: SCRIBUS_APP if given, the only one installed, or the one chosen in a list
scribus_apps=${SCRIBUS_APP:-$(find /Applications "$HOME/Applications" -maxdepth 3 -name "Scribus*.app" -type d 2>/dev/null)}
count=$(printf '%s\n' "$scribus_apps" | grep -c .)
if [ "$count" -eq 0 ]; then
    osascript -e 'display alert "Scribus introuvable" message "Installez Scribus dans le dossier Applications, puis recommencez."'
    exit 1
elif [ "$count" -eq 1 ]; then
    scribus="$scribus_apps"
else
    list=""
    while IFS= read -r a; do
        version=$(/usr/libexec/PlistBuddy -c "Print CFBundleShortVersionString" "$a/Contents/Info.plist" 2>/dev/null)
        list="$list\"$a ($version)\", "
    done <<EOF
$scribus_apps
EOF
    choice=$(osascript -e "choose from list {${list%, }} with prompt \"Quel Scribus utiliser pour le livre photo ?\" default items {}") || exit 1
    [ "$choice" = "false" ] && exit 1
    scribus="${choice% (*}"
fi

# the application, written in AppleScript
tmp=$(mktemp -d)
cat > "$tmp/Livre photo.applescript" <<EOF
-- Livre photo: opens Scribus with PhotoBookWebGUI (made by "Créer l'icône Livre photo.command")
property scribusApp : "$scribus"
property photoBookScript : "$script"

on run
	launchBook({})
end run

-- books (.sla) dropped on the icon
on open theFiles
	launchBook(theFiles)
end open

on launchBook(theFiles)
	tell application "System Events" to set scribusOpen to exists (processes whose name is "Scribus")
	if scribusOpen then
		display alert "Scribus est déjà ouvert" message "Dans Scribus, choisissez Script > Recent Scripts > PhotoBookWebGUI.py (ou Script > Execute Script… la première fois). Ou quittez Scribus et ouvrez à nouveau Livre photo."
		return
	end if
	set books to ""
	repeat with f in theFiles
		set p to POSIX path of f
		if p ends with ".sla" then set books to books & " " & quoted form of p
	end repeat
	do shell script "open -a " & quoted form of scribusApp & " --args" & books & " -py " & quoted form of photoBookScript
end launchBook
EOF
mkdir -p "$HOME/Applications"
rm -rf "$app"
osacompile -o "$app" "$tmp/Livre photo.applescript" || exit 1
# the icon of Scribus, and Scribus books accepted by drag and drop
icon=$(ls "$scribus/Contents/Resources/"*.icns 2>/dev/null | head -1)
if [ -n "$icon" ]; then
    cp "$icon" "$app/Contents/Resources/applet.icns"
    rm -f "$app/Contents/Resources/Assets.car"    # else recent macOS show the default icon
    /usr/libexec/PlistBuddy -c "Delete :CFBundleIconName" "$app/Contents/Info.plist" 2>/dev/null
fi
/usr/libexec/PlistBuddy -c "Delete :CFBundleDocumentTypes" "$app/Contents/Info.plist" 2>/dev/null
/usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes array" \
    -c "Add :CFBundleDocumentTypes:0 dict" \
    -c "Add :CFBundleDocumentTypes:0:CFBundleTypeName string Scribus" \
    -c "Add :CFBundleDocumentTypes:0:CFBundleTypeRole string Viewer" \
    -c "Add :CFBundleDocumentTypes:0:CFBundleTypeExtensions array" \
    -c "Add :CFBundleDocumentTypes:0:CFBundleTypeExtensions:0 string sla" "$app/Contents/Info.plist"
codesign --force --sign - "$app" 2>/dev/null    # signed again after the changes
touch "$app"
rm -rf "$tmp"

open -R "$app"
osascript -e 'display notification "Glissez-la dans le Dock pour l’avoir toujours sous la main." with title "Application Livre photo créée"'
