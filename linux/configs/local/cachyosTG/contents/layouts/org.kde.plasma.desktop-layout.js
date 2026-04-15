var plasma = getApiVersion(1);

var layout = {
    "desktops": [
        {
            "applets": [
                {
                    "config": {
                        "/Appearance": {
                            "clockFontColor": "72,148,114",
                            "clockFontFamily": "Okami",
                            "clockItalicText": "true",
                            "dateFontColor": "72,148,114",
                            "dateFontFamily": "Okami",
                            "dayFontColor": "211,205,205",
                            "dayFontFamily": "Earth Theory",
                            "dayItalicText": "true"
                        },
                        "/ConfigDialog": {
                            "DialogHeight": "630",
                            "DialogWidth": "810"
                        }
                    },
                    "geometry.height": 0,
                    "geometry.width": 0,
                    "geometry.x": 0,
                    "geometry.y": 0,
                    "plugin": "org.kde.plasma.clearclock",
                    "title": "ClearClock"
                }
            ],
            "config": {
                "/": {
                    "ItemGeometries-1920x1080": "Applet-71:0,336,624,352,0;",
                    "ItemGeometriesHorizontal": "Applet-71:0,336,624,352,0;",
                    "formfactor": "0",
                    "immutability": "1",
                    "lastScreen": "0",
                    "wallpaperplugin": "luisbocanegra.smart.video.wallpaper.reborn"
                },
                "/Wallpaper/luisbocanegra.smart.video.wallpaper.reborn/General": {
                    "FillMode": "0",
                    "LastVideo": "file:///home/matt/Descargas/aloneCat.mp4",
                    "LastVideoPosition": "11116",
                    "VideoUrls": "[{\"filename\":\"file:///home/matt/Descargas/aloneCat.mp4\",\"enabled\":true,\"duration\":0,\"customDuration\":0,\"playbackRate\":0,\"alternativePlaybackRate\":0,\"loop\":false},{\"filename\":\"file:///home/matt/Descargas/Chillhop.mp4\",\"enabled\":false,\"duration\":0,\"customDuration\":0,\"playbackRate\":0,\"alternativePlaybackRate\":0,\"loop\":false},{\"filename\":\"file:///home/matt/Descargas/snorlaxSleep.mp4\",\"enabled\":false,\"duration\":0,\"customDuration\":0,\"playbackRate\":0,\"alternativePlaybackRate\":0,\"loop\":false},{\"filename\":\"file:///home/matt/Descargas/WalkingWarrior4K.mp4\",\"enabled\":false,\"duration\":0,\"customDuration\":0,\"playbackRate\":0,\"alternativePlaybackRate\":0,\"loop\":false},{\"filename\":\"file:///home/matt/Descargas/WithSharks.mp4\",\"enabled\":false,\"duration\":0,\"customDuration\":0,\"playbackRate\":0,\"alternativePlaybackRate\":0,\"loop\":false}]"
                }
            },
            "wallpaperPlugin": "luisbocanegra.smart.video.wallpaper.reborn"
        }
    ],
    "panels": [
        {
            "alignment": "center",
            "applets": [
                {
                    "config": {
                        "/General": {
                            "launchers": "applications:systemsettings.desktop,preferred://filemanager,applications:Alacritty.desktop,applications:zen.desktop"
                        }
                    },
                    "plugin": "org.kde.plasma.icontasks"
                },
                {
                    "config": {
                    },
                    "plugin": "org.kde.plasma.marginsseparator"
                }
            ],
            "config": {
                "/": {
                    "formfactor": "2",
                    "immutability": "1",
                    "lastScreen": "0",
                    "wallpaperplugin": "org.kde.image"
                }
            },
            "height": 2,
            "hiding": "autohide",
            "location": "bottom",
            "maximumLength": 96,
            "minimumLength": 96,
            "offset": 0
        },
        {
            "alignment": "center",
            "applets": [
                {
                    "config": {
                        "/": {
                            "popupHeight": "535",
                            "popupWidth": "723"
                        },
                        "/ConfigDialog": {
                            "DialogHeight": "540",
                            "DialogWidth": "720"
                        },
                        "/General": {
                            "favoritesPortedToKAstats": "true",
                            "icon": "org.cachyos.hello",
                            "systemFavorites": "suspend\\,hibernate\\,reboot\\,shutdown"
                        },
                        "/Shortcuts": {
                            "global": "Alt+F1"
                        }
                    },
                    "plugin": "org.kde.plasma.kickoff"
                },
                {
                    "config": {
                    },
                    "plugin": "org.kde.plasma.marginsseparator"
                },
                {
                    "config": {
                    },
                    "plugin": "org.kde.plasma.panelspacer"
                },
                {
                    "config": {
                        "/": {
                            "popupHeight": "400",
                            "popupWidth": "560"
                        }
                    },
                    "plugin": "org.kde.plasma.digitalclock"
                },
                {
                    "config": {
                    },
                    "plugin": "org.kde.plasma.panelspacer"
                },
                {
                    "config": {
                    },
                    "plugin": "org.kde.plasma.systemtray"
                }
            ],
            "config": {
                "/": {
                    "formfactor": "2",
                    "immutability": "1",
                    "lastScreen": "0",
                    "wallpaperplugin": "org.kde.image"
                }
            },
            "height": 2,
            "hiding": "autohide",
            "location": "top",
            "maximumLength": 96,
            "minimumLength": 96,
            "offset": 0
        }
    ],
    "serializationFormatVersion": "1"
}
;

plasma.loadSerializedLayout(layout);
