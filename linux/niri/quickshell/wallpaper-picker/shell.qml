//@ pragma ShellId wallpaper-picker

import QtQuick
import QtQuick.Effects
import Quickshell
import Quickshell.Io

ShellRoot {
    id: root

    // Cambia esta ruta si más adelante decides guardar los fondos en otro lugar.
    property string wallpapersDirectory: {
        const home = Quickshell.env("HOME")
        return (home ? home : "") + "/Descargas/Wallpapers"
    }

    property var wallpapers: []
    property string selectedWallpaper: ""
    property bool scanning: false

    // Dimensiones pensadas para que se vean ~4 wallpapers a la vez, cómodos y grandes.
    readonly property int thumbnailWidth: 230
    readonly property int thumbnailHeight: 145
    readonly property int itemSpacing: 16
    readonly property int contentMargin: 18
    readonly property int visibleCount: 4

    function displayName(path: string): string {
        const name = path.substring(path.lastIndexOf("/") + 1)
        return name.replace(/\.[^/.]+$/, "")
    }

    // Image.source necesita una URL; codificar por segmentos conserva las barras.
    function fileUrl(path: string): string {
        return "file://" + path.split("/").map(encodeURIComponent).join("/")
    }

    function loadWallpapers(): void {
        if (scanning)
            return

        scanning = true

        scanner.exec([
            "find", wallpapersDirectory,
            "-type", "f", "(",
            "-iname", "*.jpg", "-o", "-iname", "*.jpeg", "-o",
            "-iname", "*.png", "-o", "-iname", "*.webp", "-o",
            "-iname", "*.avif", "-o", "-iname", "*.bmp", "-o",
            "-iname", "*.gif",
            ")", "-print0"
        ])
    }

    function acceptScan(output: string): void {
        const paths = output.split("\u0000").filter(path => path.length > 0)

        paths.sort((a, b) =>
            displayName(a).localeCompare(displayName(b))
        )

        wallpapers = paths
        scanning = false
    }

    function chooseWallpaper(path: string): void {
        selectedWallpaper = path
        wallpaperSetter.exec([
            "noctalia",
            "msg",
            "wallpaper-set",
            path
        ])
    }

    function moveSelection(step: int): void {
        if (wallpapers.length === 0)
            return

        const current = wallpapers.indexOf(selectedWallpaper)

        const index = current < 0
                    ? (step > 0 ? 0 : wallpapers.length - 1)
                    : (current + step + wallpapers.length) % wallpapers.length

        selectedWallpaper = wallpapers[index]
    }

    Component.onCompleted: loadWallpapers()

    Process {
        id: scanner

        stdout: StdioCollector {
            onStreamFinished: root.acceptScan(text)
        }

        onExited: function(exitCode) {
            if (exitCode !== 0)
                root.scanning = false
        }
    }

    Process {
        id: wallpaperSetter
    }

    Variants {
        // En Quickshell 0.3.1 (el paquete actual de CachyOS/Arch)
        // Variants recibe la colección mediante `model`.
        model: Quickshell.screens

        PanelWindow {
            id: panelWindow
            required property var modelData

            screen: modelData
            visible: true
            color: "transparent"
            focusable: true
            aboveWindows: true
            exclusionMode: ExclusionMode.Ignore

            implicitHeight: root.thumbnailHeight
                              + root.contentMargin * 2
                              + 30

            anchors {
                left: true
                right: true
                bottom: true
            }

            margins.bottom: 24

            // El panel ocupa todo el ancho para poder centrarse, pero solo esta
            // región recibe clics. El resto continúa llegando a Niri/las ventanas.
            mask: Region {
                item: picker
                radius: 22
            }

            Rectangle {
                id: picker

                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom

                width: Math.min(
                    parent.width - 48,
                    root.thumbnailWidth * root.visibleCount
                    + root.itemSpacing * (root.visibleCount - 1)
                    + root.contentMargin * 2
                )

                height: root.thumbnailHeight + root.contentMargin * 2

                radius: 22
                color: "#dc11151f"

                border.width: 1
                border.color: "#4dffffff"

                clip: true
                focus: true

                Behavior on width {
                    NumberAnimation {
                        duration: 180
                        easing.type: Easing.OutCubic
                    }
                }

                Keys.onPressed: function(event) {
                    if (event.key === Qt.Key_Left) {
                        root.moveSelection(-1)
                        event.accepted = true

                    } else if (event.key === Qt.Key_Right) {
                        root.moveSelection(1)
                        event.accepted = true

                    } else if (
                        event.key === Qt.Key_Return ||
                        event.key === Qt.Key_Enter
                    ) {
                        if (root.selectedWallpaper)
                            root.chooseWallpaper(root.selectedWallpaper)

                        event.accepted = true

                    } else if (event.key === Qt.Key_R) {
                        root.loadWallpapers()
                        event.accepted = true
                    }
                }

                Rectangle {
                    anchors.fill: parent
                    radius: parent.radius

                    color: "transparent"

                    border.width: 1
                    border.color: "#1affffff"
                }

                Item {
                    anchors.fill: parent
                    anchors.margins: root.contentMargin

                    Text {
                        anchors.centerIn: parent

                        visible: !root.scanning
                                 && root.wallpapers.length === 0

                        text: "Añade imágenes a ~/Descargas/Wallpapers"

                        color: "#aeb7c5"
                        font.pixelSize: 14
                    }

                    ListView {
                        id: chooserPositioner

                        anchors.fill: parent

                        visible: root.wallpapers.length > 0

                        orientation: ListView.Horizontal
                        spacing: root.itemSpacing
                        clip: true

                        boundsBehavior: Flickable.StopAtBounds
                        model: root.wallpapers

                        Connections {
                            target: root

                            function onSelectedWallpaperChanged(): void {
                                const index = root.wallpapers.indexOf(
                                    root.selectedWallpaper
                                )

                                if (index < 0)
                                    return

                                const itemWidth =
                                    root.thumbnailWidth + root.itemSpacing

                                const itemStart = index * itemWidth
                                const itemEnd =
                                    itemStart + root.thumbnailWidth

                                const visibleStart =
                                    chooserPositioner.contentX

                                const visibleEnd =
                                    visibleStart + chooserPositioner.width

                                // La imagen ya está completamente visible.
                                // No movemos el carrusel.
                                if (
                                    itemStart >= visibleStart &&
                                    itemEnd <= visibleEnd
                                ) {
                                    return
                                }

                                // La imagen quedó a la derecha.
                                if (itemEnd > visibleEnd) {
                                    const targetX =
                                        itemEnd - chooserPositioner.width

                                    const maxX = Math.max(
                                        0,
                                        chooserPositioner.contentWidth
                                        - chooserPositioner.width
                                    )

                                    chooserPositioner.contentX =
                                        Math.min(targetX, maxX)

                                // La imagen quedó a la izquierda.
                                } else if (itemStart < visibleStart) {
                                    chooserPositioner.contentX = itemStart
                                }
                            }
                        }

                        // El scroll del mouse en Linux llega como rueda vertical;
                        // lo traducimos a desplazamiento horizontal.
                        WheelHandler {
                            target: null

                            onWheel: function(event) {
                                const delta =
                                    event.angleDelta.y !== 0
                                    ? event.angleDelta.y
                                    : -event.angleDelta.x

                                const maxX = Math.max(
                                    0,
                                    chooserPositioner.contentWidth
                                    - chooserPositioner.width
                                )

                                chooserPositioner.contentX = Math.max(
                                    0,
                                    Math.min(
                                        maxX,
                                        chooserPositioner.contentX - delta
                                    )
                                )
                            }
                        }

                        // Solo anima los saltos programáticos.
                        // El arrastre manual conserva su física normal.
                        Behavior on contentX {
                            enabled: !chooserPositioner.moving

                            NumberAnimation {
                                duration: 420
                                easing.type: Easing.OutCubic
                            }
                        }

                        delegate: Item {
                            id: wallpaperDelegate

                            required property string modelData
                            required property int index

                            readonly property bool isSelected:
                                root.selectedWallpaper === modelData

                            width: root.thumbnailWidth

                            height: Math.min(
                                root.thumbnailHeight,
                                chooserPositioner.height
                            )

                            scale: hoverArea.containsMouse
                                   ? 1.025
                                   : 1.0

                            Behavior on scale {
                                NumberAnimation {
                                    duration: 120
                                    easing.type: Easing.OutCubic
                                }
                            }

                            Rectangle {
                                id: thumbnailFrame

                                anchors.fill: parent

                                radius: 13
                                antialiasing: true

                                color: wallpaperDelegate.isSelected
                                       ? "#26314a"
                                       : "#202733"

                                border.width:
                                    wallpaperDelegate.isSelected ? 3 : 1

                                border.color:
                                    wallpaperDelegate.isSelected
                                    ? "#8ec3ff"
                                    : (
                                        hoverArea.containsMouse
                                        ? "#9affffff"
                                        : "#35ffffff"
                                    )

                                Behavior on border.color {
                                    ColorAnimation {
                                        duration: 130
                                    }
                                }

                                Behavior on color {
                                    ColorAnimation {
                                        duration: 130
                                    }
                                }

                                Item {
                                    id: imageArea

                                    anchors.fill: parent
                                    anchors.margins:
                                        thumbnailFrame.border.width

                                    Image {
                                        id: thumbnail

                                        anchors.fill: parent

                                        source:
                                            root.fileUrl(
                                                wallpaperDelegate.modelData
                                            )

                                        fillMode: Image.PreserveAspectCrop

                                        asynchronous: true
                                        cache: true
                                        smooth: true
                                        mipmap: true

                                        visible: false
                                    }

                                    Item {
                                        id: thumbnailMask

                                        anchors.fill: parent

                                        // MultiEffect necesita poder usar
                                        // este Item como textura.
                                        layer.enabled: true
                                        layer.smooth: true

                                        visible: false

                                        Rectangle {
                                            anchors.fill: parent

                                            color: "white"

                                            radius: 11
                                            antialiasing: true
                                        }
                                    }

                                    MultiEffect {
                                        id: thumbnailEffect

                                        anchors.fill: imageArea

                                        source: thumbnail

                                        maskEnabled: true
                                        maskSource: thumbnailMask

                                        maskThresholdMin: 0.5
                                        maskSpreadAtMin: 0.05
                                    }

                                    Text {
                                        anchors.centerIn: parent

                                        visible:
                                            thumbnail.status === Image.Error

                                        text: "No se pudo\ncargar"

                                        horizontalAlignment:
                                            Text.AlignHCenter

                                        color: "#d7deea"
                                        font.pixelSize: 12
                                    }
                                }
                            }

                            HoverHandler {
                                id: hoverArea
                            }

                            TapHandler {
                                onTapped:
                                    root.chooseWallpaper(
                                        wallpaperDelegate.modelData
                                    )
                            }
                        }
                    }
                }
            }
        }
    }
}
