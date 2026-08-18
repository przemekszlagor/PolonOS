// PolonOS Plasma Desktop Layout Configuration
var panel = new Panel;
panel.location = "bottom";
panel.height = 44;
panel.alignment = "center";

// 1. Kickoff Start Menu with PolonOS Logo Icon
var kickoff = panel.addWidget("org.kde.plasma.kickoff");
kickoff.currentConfigGroup = ["General"];
kickoff.writeConfig("icon", "start-here");

// 2. Icons-Only Task Manager
var taskManager = panel.addWidget("org.kde.plasma.icontasks");

// 3. System Tray
var systemTray = panel.addWidget("org.kde.plasma.systemtray");

// 4. Digital Clock
var clock = panel.addWidget("org.kde.plasma.digitalclock");

// Configure Desktop Wallpaper for all screens
var desktopsArray = desktops();
for (var i = 0; i < desktopsArray.length; i++) {
    var d = desktopsArray[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
    d.writeConfig("Image", "file:///usr/share/wallpapers/PolonOS/contents/images/1920x1080.png");
}
